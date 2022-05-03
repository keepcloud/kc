"""KeepCloud bootstrapping."""

# All built-in application controllers should be imported, and registered
# in this file in the same way as KCBaseController.


from kc.cli.controllers.base import KCBaseController


def load(app):
    app.handler.register(KCBaseController)
