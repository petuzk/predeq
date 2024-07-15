from hypothesis import HealthCheck, settings


# disable HealthCheck.too_slow for GitHub Actions because it often times out randomly
settings.register_profile('ci', suppress_health_check=[HealthCheck.too_slow])
