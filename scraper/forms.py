from django import forms
from .models import ScrapeJob


ATTRIBUTE_CHOICES = [
    ('text', 'Inner Text'),
    ('href', 'href (links)'),
    ('src',  'src (images/media)'),
    ('alt',  'alt (image alt text)'),
    ('title', 'title attribute'),
    ('data-value', 'data-value attribute'),
    ('class', 'class attribute'),
    ('id',   'id attribute'),
]


class ScrapeJobForm(forms.ModelForm):
    """Form for creating / editing a ScrapeJob."""

    extract_attribute = forms.ChoiceField(
        choices=ATTRIBUTE_CHOICES,
        initial='text',
        label='Extract',
        help_text='What to pull from each matched element.',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = ScrapeJob
        fields = ['name', 'url', 'css_selector', 'extract_attribute', 'headers']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Quotes Scraper',
            }),
            'url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com',
            }),
            'css_selector': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. h1, .product-title, #main p',
            }),
            'headers': forms.Textarea(attrs={
                'class': 'form-control font-monospace',
                'rows': 3,
                'placeholder': '{"Authorization": "Bearer token123"}',
            }),
        }
        labels = {
            'css_selector': 'CSS Selector',
            'headers': 'Custom Headers (JSON, optional)',
        }
        help_texts = {
            'url': 'The full URL of the page to scrape.',
            'css_selector': 'CSS selector targeting elements (e.g. h2.title, ul > li, a[href])',
            'headers': 'Optional HTTP headers in JSON format.',
        }

    def clean_headers(self):
        """Validate that headers field is valid JSON if provided."""
        import json
        headers = self.cleaned_data.get('headers', '').strip()
        if not headers:
            return ''
        try:
            parsed = json.loads(headers)
            if not isinstance(parsed, dict):
                raise forms.ValidationError('Headers must be a JSON object (dict), e.g. {"key": "value"}.')
            return json.dumps(parsed, indent=2)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError(f'Invalid JSON: {exc}')

    def clean_css_selector(self):
        """Basic validation of CSS selector."""
        selector = self.cleaned_data.get('css_selector', '').strip()
        if not selector:
            raise forms.ValidationError('CSS selector cannot be empty.')
        return selector
