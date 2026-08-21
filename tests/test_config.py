from app.config import settings


def test_settings_load():
    """
    Test that application settings load with default values.
    """
    assert settings.APP_NAME == "JobPilot"
    assert settings.PORT == 8000
    assert isinstance(settings.cors_origins_list, list)
    assert len(settings.cors_origins_list) > 0
