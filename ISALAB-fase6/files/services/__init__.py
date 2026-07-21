"""Service layer for IsaLab — business logic that sits between the GUI
and the repositories. Each service wraps one or more repositories and
enforces RBAC (``utils.security.Authorizer``), validation
(``utils.validators`` / Pydantic schemas) and audit logging.
"""
