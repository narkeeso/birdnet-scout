from . import models


def global_context(request):
    return {"config": models.Config.config.get_config()}
