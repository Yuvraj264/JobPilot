from typing import List, Dict, Any
from playwright.sync_api import Page


class PageInspector:
    """
    Page Inspector extracting structured DOM input element representations without sending raw HTML to external APIs.
    """

    @staticmethod
    def inspect_page(page: Page) -> List[Dict[str, Any]]:
        if not page:
            return []

        # Execute in-browser script to inspect input, select, textarea, and file elements
        script = """
        () => {
            const elements = [];
            const formInputs = document.querySelectorAll('input, select, textarea');
            
            formInputs.forEach((el) => {
                const tag = el.tagName.toLowerCase();
                const type = (el.type || 'text').toLowerCase();
                const name = el.name || '';
                const id = el.id || '';
                const placeholder = el.placeholder || '';
                const required = el.required || false;
                
                // Find associated label
                let labelText = '';
                if (id) {
                    const labelEl = document.querySelector(`label[for="${id}"]`);
                    if (labelEl) labelText = labelEl.innerText ? labelEl.innerText.trim() : '';
                }
                if (!labelText) {
                    const parentLabel = el.closest('label');
                    if (parentLabel) labelText = parentLabel.innerText;
                }

                // Options for select elements
                const options = [];
                if (tag === 'select') {
                    Array.from(el.options).forEach(opt => {
                        if (opt.value) options.push({ label: opt.innerText, value: opt.value });
                    });
                }

                elements.push({
                    tag_name: tag,
                    input_type: type,
                    name: name,
                    id: id,
                    label: labelText.trim(),
                    placeholder: placeholder,
                    required: required,
                    options: options,
                });
            });

            // Detect CAPTCHA presence
            const hasCaptcha = document.querySelector('.g-recaptcha, iframe[src*="captcha"], #captcha') !== null;

            return {
                elements: elements,
                has_captcha: hasCaptcha,
                title: document.title,
                url: window.location.href,
            };
        }
        """

        try:
            res = page.evaluate(script)
            return res
        except Exception as err:
            return {"elements": [], "has_captcha": False, "title": page.title(), "url": page.url}
