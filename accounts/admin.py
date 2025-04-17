from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, UserProfile, BioData, Account, Transaction, NINDatabase, BVNDatabase

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

class CustomUserAdmin(BaseUserAdmin):
    model = CustomUser
    list_display = ('email', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'date_joined')
    search_fields = ('email', 'nin', 'bvn')
    ordering = ('-date_joined',)
    inlines = [UserProfileInline]
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Verification', {'fields': ('nin', 'bvn', 'pin')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )

@admin.register(BioData)
class BioDataAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'nin', 'bvn', 'date_of_birth', 'verified_on')
    search_fields = ('first_name', 'last_name', 'nin', 'bvn')
    list_filter = ('verified_on',)

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'account_number', 'balance')
    search_fields = ('user__email', 'account_number')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('account', 'amount', 'transaction_type', 'timestamp')
    search_fields = ('account__account_number', 'transaction_type')
    list_filter = ('transaction_type', 'timestamp')

@admin.register(NINDatabase)
class NINDatabaseAdmin(admin.ModelAdmin):
    list_display = ('nin', 'first_name', 'last_name', 'date_of_birth')
    search_fields = ('nin', 'first_name', 'last_name')

@admin.register(BVNDatabase)
class BVNDatabaseAdmin(admin.ModelAdmin):
    list_display = ('bvn', 'first_name', 'last_name', 'date_of_birth')
    search_fields = ('bvn', 'first_name', 'last_name')

# Register CustomUser with custom admin
admin.site.register(CustomUser, CustomUserAdmin)
