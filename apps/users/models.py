import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email address is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "ADMIN")
        extra_fields.setdefault("is_verified", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):

    class Role(models.TextChoices):
        BUYER        = "BUYER",        "Buyer"
        SHOPKEEPER   = "SHOPKEEPER",   "Shopkeeper"
        DELIVERY_BOY = "DELIVERY_BOY", "Delivery Boy"
        ADMIN        = "ADMIN",        "Admin"
        STAFF        = "STAFF",        "QabiFly Staff"

    class AuthProvider(models.TextChoices):
        EMAIL  = "EMAIL",  "Email & Password"
        GOOGLE = "GOOGLE", "Google"

    id       = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email    = models.EmailField(unique=True)
    phone    = models.CharField(max_length=15, blank=True, null=True, unique=True)

    # Virtual Number System
    virtual_number    = models.CharField(
        max_length=20, unique=True, null=True, blank=True
    )
    station_code      = models.CharField(max_length=5, blank=True)
    virtual_name      = models.CharField(max_length=100, blank=True)
    virtual_photo     = models.ImageField(
        upload_to="virtual_profiles/", blank=True, null=True
    )
    onboarding_complete = models.BooleanField(default=False)

    # Location
    village   = models.CharField(max_length=100, blank=True)
    district  = models.CharField(max_length=100, blank=True)
    state     = models.CharField(max_length=100, blank=True, default="Uttar Pradesh")
    pincode   = models.CharField(max_length=10, blank=True)

    # Auth
    auth_provider     = models.CharField(
        max_length=10,
        choices=AuthProvider.choices,
        default=AuthProvider.EMAIL,
    )
    google_id         = models.CharField(max_length=200, blank=True, null=True, unique=True)

    full_name         = models.CharField(max_length=150, blank=True)
    role              = models.CharField(
        max_length=20, choices=Role.choices, default=Role.BUYER
    )
    profile_photo     = models.ImageField(
        upload_to="profiles/", blank=True, null=True
    )
    is_verified       = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    is_active         = models.BooleanField(default=True)
    is_staff          = models.BooleanField(default=False)
    date_of_birth     = models.DateField(blank=True, null=True)
    city              = models.CharField(max_length=100, blank=True, default="Reoti")
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = []
    objects         = UserManager()

    class Meta:
        db_table     = "users"
        ordering     = ["-created_at"]
        verbose_name = "User"

    def __str__(self):
        return f"{self.virtual_number or self.email} ({self.role})"

    @property
    def is_buyer(self):
        return self.role == self.Role.BUYER

    @property
    def is_shopkeeper(self):
        return self.role == self.Role.SHOPKEEPER

    @property
    def is_delivery_boy(self):
        return self.role == self.Role.DELIVERY_BOY

    @property
    def is_admin_user(self):
        return self.role == self.Role.ADMIN

    @property
    def display_name(self):
        return self.virtual_name or self.full_name or "QabiFly User"


class KYCDocument(models.Model):

    class DocType(models.TextChoices):
        AADHAAR = "AADHAAR", "Aadhaar Card"
        PAN     = "PAN",     "PAN Card"

    class Status(models.TextChoices):
        PENDING  = "PENDING",  "Pending Review"
        VERIFIED = "VERIFIED", "Verified"
        REJECTED = "REJECTED", "Rejected"

    id               = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    user             = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="kyc_documents"
    )
    doc_type         = models.CharField(max_length=10, choices=DocType.choices)
    doc_number       = models.CharField(max_length=20)
    doc_file         = models.FileField(upload_to="kyc/documents/")
    selfie           = models.ImageField(
        upload_to="kyc/selfies/", blank=True, null=True
    )
    status           = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    rejection_reason = models.TextField(blank=True)
    verified_by      = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="kyc_verifications",
    )
    verified_at      = models.DateTimeField(null=True, blank=True)
    submitted_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = "kyc_documents"
        unique_together = [("user", "doc_type")]

    def __str__(self):
        return f"{self.user.email} — {self.doc_type} — {self.status}"