from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.profile import UserProfile
from app.models.resume import Resume
from app.models.screening import ApplicationQuestion, ApplicationAnswer, AnswerMemory
from app.services.screening.taxonomy import QuestionType
from app.services.screening.question_classifier import QuestionClassifier
from app.services.screening.answer_source_resolver import AnswerSourceResolver
from app.services.screening.answer_generator import AnswerGenerator
from app.services.screening.answer_validator import AnswerValidator


class QuestionProcessingService:
    """
    Question Processing Service orchestrating the Screening Question pipeline:
    Question -> Classifier -> Source Resolver -> Memory Lookup -> Generator -> Validator -> DB Persistence
    """

    def __init__(self, answer_generator=None):
        self.generator = answer_generator or AnswerGenerator()

    def process_question(
        self,
        db: Session,
        question_text: str,
        profile: UserProfile,
        job_context: Dict[str, Any],
        automation_run_id: Optional[int] = None,
        job_id: Optional[int] = None,
        field_identifier: Optional[str] = None,
        required: bool = True,
        max_length: Optional[int] = None,
        resume: Optional[Resume] = None,
        require_human_review: bool = True
    ) -> Dict[str, Any]:

        # 1. Classification
        cls = QuestionClassifier.classify_question(question_text, field_identifier=field_identifier or "")
        q_type = cls["type"]
        q_conf = cls["confidence"]
        is_sensitive = cls["is_sensitive"]

        # 2. Source Resolution
        source = AnswerSourceResolver.resolve_source(q_type, question_text)

        # 3. Save ApplicationQuestion DB record
        question_rec = ApplicationQuestion(
            automation_run_id=automation_run_id,
            job_id=job_id,
            question_text=question_text,
            field_identifier=field_identifier,
            question_type=q_type,
            required=required,
            classification_confidence=q_conf,
            answer_source=source,
            max_length=max_length,
            is_sensitive=is_sensitive,
        )
        db.add(question_rec)
        db.commit()
        db.refresh(question_rec)

        # 4. Check Reusable Answer Memory
        mem = db.query(AnswerMemory).filter(
            AnswerMemory.profile_id == profile.id,
            AnswerMemory.question_text == question_text,
            AnswerMemory.user_approved == True,
            AnswerMemory.reusable == True
        ).first()

        if mem:
            ans_rec = ApplicationAnswer(
                question_id=question_rec.id,
                answer_text=mem.answer_text,
                answer_status="HUMAN_PROVIDED" if not require_human_review else "NEEDS_REVIEW",
                confidence=0.99,
                generated_by="HUMAN",
                validation_result={"valid": True, "reused_from_memory": True}
            )
            db.add(ans_rec)
            db.commit()
            return {
                "question_id": question_rec.id,
                "answer_id": ans_rec.id,
                "question_type": q_type,
                "answer_text": mem.answer_text,
                "status": ans_rec.answer_status,
                "confidence": 0.99,
                "requires_human": require_human_review,
                "reason": "Reused from approved AnswerMemory (requires review per config)." if require_human_review else None
            }

        # 5. Low Classification Confidence -> Request Human Review
        if q_conf < 0.70 or q_type == QuestionType.UNKNOWN:
            ans_rec = ApplicationAnswer(
                question_id=question_rec.id,
                answer_text=None,
                answer_status="NEEDS_REVIEW",
                confidence=q_conf,
                generated_by="SYSTEM",
                validation_result={"valid": False, "reason": "Low classification confidence."}
            )
            db.add(ans_rec)
            db.commit()
            return {
                "question_id": question_rec.id,
                "answer_id": ans_rec.id,
                "question_type": q_type,
                "answer_text": None,
                "status": "NEEDS_REVIEW",
                "confidence": q_conf,
                "requires_human": True,
                "reason": f"Ambiguous question type ('{q_type}') with low confidence ({q_conf})."
            }

        # 6. Generate Answer
        gen_res = self.generator.generate(
            question_text, q_type, source, profile, job_context, resume=resume, max_length=max_length
        )

        if gen_res.get("status") == "INSUFFICIENT_INFORMATION":
            ans_rec = ApplicationAnswer(
                question_id=question_rec.id,
                answer_text=None,
                answer_status="INSUFFICIENT_INFORMATION",
                confidence=0.0,
                generated_by="SYSTEM",
                validation_result={"valid": False, "reason": gen_res.get("reason")}
            )
            db.add(ans_rec)
            db.commit()
            return {
                "question_id": question_rec.id,
                "answer_id": ans_rec.id,
                "question_type": q_type,
                "answer_text": None,
                "status": "INSUFFICIENT_INFORMATION",
                "confidence": 0.0,
                "requires_human": True,
                "reason": gen_res.get("reason")
            }

        # 7. Validate Answer
        ans_text = gen_res["answer"]
        val_res = AnswerValidator.validate_answer(ans_text, question_text, max_length=max_length, confidence=gen_res["confidence"])

        final_status = "NEEDS_REVIEW" if (require_human_review or not val_res["valid"]) else "VALIDATED"

        ans_rec = ApplicationAnswer(
            question_id=question_rec.id,
            answer_text=ans_text,
            answer_status=final_status,
            confidence=val_res["confidence"],
            generated_by=gen_res.get("generated_by", "DETERMINISTIC"),
            validation_result=val_res
        )
        db.add(ans_rec)
        db.commit()

        return {
            "question_id": question_rec.id,
            "answer_id": ans_rec.id,
            "question_type": q_type,
            "answer_text": ans_text,
            "status": final_status,
            "confidence": val_res["confidence"],
            "requires_human": final_status == "NEEDS_REVIEW",
            "reason": "Human review required per user preference configuration." if final_status == "NEEDS_REVIEW" else None
        }
