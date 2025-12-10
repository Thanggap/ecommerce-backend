# i18n Message Keys
# Frontend will translate these keys using react-i18next
# Format: namespace.key_name

class I18nKeys:
    """
    Centralized i18n keys for API responses.
    Frontend uses these keys with t() function to display translated messages.
    """

    # Auth messages
    AUTH_LOGIN_SUCCESS = "auth.login_success"
    AUTH_LOGOUT_SUCCESS = "auth.logout_success"
    AUTH_REGISTER_SUCCESS = "auth.register_success"
    AUTH_INVALID_CREDENTIALS = "auth.invalid_credentials"
    AUTH_EMAIL_ALREADY_EXISTS = "auth.email_already_exists"
    AUTH_TOKEN_INVALID = "auth.token_invalid"
    AUTH_ACCOUNT_DISABLED = "auth.account_disabled"
    AUTH_ADMIN_ONLY = "auth.admin_only"
    AUTH_LOGIN_REQUIRED = "auth.login_required"
    AUTH_RESET_EMAIL_SENT = "auth.reset_email_sent"
    AUTH_INVALID_RESET_TOKEN = "auth.invalid_reset_token"
    AUTH_RESET_TOKEN_EXPIRED = "auth.reset_token_expired"
    AUTH_PASSWORD_RESET_SUCCESS = "auth.password_reset_success"

    # User messages
    USER_NOT_FOUND = "user.not_found"
    USER_ALREADY_ADMIN = "user.already_admin"
    USER_ALREADY_USER = "user.already_user"
    USER_PROMOTED = "user.promoted_to_admin"
    USER_DEMOTED = "user.demoted_to_user"
    USER_CANNOT_DEMOTE_SELF = "user.cannot_demote_self"

    # Profile messages
    PROFILE_UPDATED = "profile.updated"
    PROFILE_PASSWORD_CHANGED = "profile.password_changed"
    PROFILE_WRONG_PASSWORD = "profile.wrong_password"

    # Product messages
    PRODUCT_NOT_FOUND = "product.not_found"
    PRODUCT_CREATED = "product.created"
    PRODUCT_UPDATED = "product.updated"
    PRODUCT_DELETED = "product.deleted"
    PRODUCT_ADDED_TO_CART = "product.added_to_cart"
    PRODUCT_FETCH_ERROR = "product.fetch_error"

    # Cart messages
    CART_ITEM_ADDED = "cart.item_added"
    CART_ITEM_REMOVED = "cart.item_removed"
    CART_ITEM_UPDATED = "cart.item_updated"
    CART_EMPTY = "cart.empty"
    CART_OUT_OF_STOCK = "cart.out_of_stock"
    CART_ITEM_NOT_FOUND = "cart.item_not_found"

    # Order messages
    ORDER_CREATED = "order.created"
    ORDER_NOT_FOUND = "order.not_found"
    ORDER_STATUS_UPDATED = "order.status_updated"
    ORDER_CHECKOUT_SUCCESS = "order.checkout_success"
    ORDER_PAYMENT_FAILED = "order.payment_failed"

    # Review messages
    REVIEW_POSTED = "review.posted"
    REVIEW_DELETED = "review.deleted"
    REVIEW_NOT_FOUND = "review.not_found"
    REVIEW_ALREADY_EXISTS = "review.already_exists"
    REVIEW_PURCHASE_REQUIRED = "review.purchase_required"

    # General messages
    GENERAL_SUCCESS = "general.success"
    GENERAL_ERROR = "general.error"
    GENERAL_NOT_FOUND = "general.not_found"
    GENERAL_FORBIDDEN = "general.forbidden"
    GENERAL_BAD_REQUEST = "general.bad_request"

    # Upload messages
    UPLOAD_SUCCESS = "upload.success"
    UPLOAD_FAILED = "upload.failed"
    UPLOAD_INVALID_TYPE = "upload.invalid_type"
