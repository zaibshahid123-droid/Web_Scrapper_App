from django.contrib import admin
from .models import ScrapeJob, ScrapeResult


class ScrapeResultInline(admin.TabularInline):
    model = ScrapeResult
    extra = 0
    readonly_fields = ('element_index', 'element_tag', 'content', 'scraped_at')
    can_delete = True
    max_num = 50
    show_change_link = False


@admin.register(ScrapeJob)
class ScrapeJobAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'url_short', 'css_selector', 'status', 'result_count', 'last_run_at', 'created_at')
    list_filter = ('status', 'user', 'created_at')
    search_fields = ('name', 'url', 'css_selector', 'user__username')
    readonly_fields = ('created_at', 'updated_at', 'last_run_at', 'status', 'error_message')
    inlines = [ScrapeResultInline]
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Job Configuration', {
            'fields': ('user', 'name', 'url', 'css_selector', 'extract_attribute', 'headers'),
        }),
        ('Status & Timing', {
            'fields': ('status', 'error_message', 'last_run_at', 'created_at', 'updated_at'),
        }),
    )

    @admin.display(description='URL')
    def url_short(self, obj):
        url = obj.url
        return url[:60] + '…' if len(url) > 60 else url

    @admin.display(description='Results')
    def result_count(self, obj):
        return obj.results.count()


@admin.register(ScrapeResult)
class ScrapeResultAdmin(admin.ModelAdmin):
    list_display = ('job', 'element_index', 'element_tag', 'content_short', 'scraped_at')
    list_filter = ('job__user', 'element_tag', 'scraped_at')
    search_fields = ('content', 'job__name')
    readonly_fields = ('scraped_at',)

    @admin.display(description='Content')
    def content_short(self, obj):
        return obj.content[:80] + '…' if len(obj.content) > 80 else obj.content
