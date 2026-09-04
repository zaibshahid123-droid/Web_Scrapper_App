from django.db import models
from django.contrib.auth.models import User
import json


class ScrapeJob(models.Model):
    """Represents a scraping job configuration."""

    STATUS_CHOICES = [
        ('idle', 'Idle'),
        ('running', 'Running'),
        ('done', 'Done'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scrape_jobs')
    name = models.CharField(max_length=255, help_text='A friendly name for this job')
    url = models.URLField(max_length=2000, help_text='The URL to scrape')
    css_selector = models.CharField(
        max_length=500,
        help_text='CSS selector to target elements (e.g. h1, .title, #main p)',
    )
    extract_attribute = models.CharField(
        max_length=100,
        blank=True,
        default='text',
        help_text='Attribute to extract: "text" for inner text, or an HTML attribute like "href", "src"',
    )
    headers = models.TextField(
        blank=True,
        default='',
        help_text='Optional extra HTTP headers in JSON format (e.g. {"Accept-Language": "en-US"})',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='idle')
    error_message = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_run_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Scrape Job'
        verbose_name_plural = 'Scrape Jobs'

    def __str__(self):
        return f"{self.name} ({self.url[:60]})"

    def get_headers_dict(self):
        """Return parsed headers dict, or empty dict on failure."""
        if not self.headers.strip():
            return {}
        try:
            return json.loads(self.headers)
        except (json.JSONDecodeError, TypeError):
            return {}

    @property
    def result_count(self):
        return self.results.count()

    @property
    def status_badge_class(self):
        mapping = {
            'idle': 'secondary',
            'running': 'warning',
            'done': 'success',
            'failed': 'danger',
        }
        return mapping.get(self.status, 'secondary')


class ScrapeResult(models.Model):
    """Stores a single scraped data item linked to a ScrapeJob."""

    job = models.ForeignKey(ScrapeJob, on_delete=models.CASCADE, related_name='results')
    content = models.TextField(help_text='The scraped text or attribute value')
    element_tag = models.CharField(max_length=50, blank=True, default='')
    element_index = models.PositiveIntegerField(default=0)
    scraped_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['element_index']
        verbose_name = 'Scrape Result'
        verbose_name_plural = 'Scrape Results'

    def __str__(self):
        return f"[{self.job.name}] #{self.element_index}: {self.content[:80]}"
