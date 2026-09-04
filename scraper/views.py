import csv
import json
import logging
from datetime import timezone

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone as django_timezone
from django.views.decorators.http import require_POST

from .forms import ScrapeJobForm
from .models import ScrapeJob, ScrapeResult
from .scraper_engine import scrape_url

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Dashboard
# ──────────────────────────────────────────────────────────────────────────────
@login_required
def dashboard(request):
    """Main dashboard — lists all scrape jobs for the logged-in user."""
    jobs = ScrapeJob.objects.filter(user=request.user).order_by('-created_at')
    stats = {
        'total': jobs.count(),
        'done': jobs.filter(status='done').count(),
        'failed': jobs.filter(status='failed').count(),
        'running': jobs.filter(status='running').count(),
    }
    return render(request, 'scraper/dashboard.html', {'jobs': jobs, 'stats': stats})


# ──────────────────────────────────────────────────────────────────────────────
# Create Job
# ──────────────────────────────────────────────────────────────────────────────
@login_required
def job_create(request):
    """Create a new scrape job."""
    if request.method == 'POST':
        form = ScrapeJobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.user = request.user
            job.save()
            messages.success(request, f'Job "{job.name}" created successfully!')
            return redirect('job_detail', pk=job.pk)
    else:
        form = ScrapeJobForm()
    return render(request, 'scraper/job_form.html', {'form': form, 'action': 'Create'})


# ──────────────────────────────────────────────────────────────────────────────
# Edit Job
# ──────────────────────────────────────────────────────────────────────────────
@login_required
def job_edit(request, pk):
    """Edit an existing scrape job."""
    job = get_object_or_404(ScrapeJob, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ScrapeJobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, f'Job "{job.name}" updated successfully!')
            return redirect('job_detail', pk=job.pk)
    else:
        form = ScrapeJobForm(instance=job)
    return render(request, 'scraper/job_form.html', {'form': form, 'action': 'Edit', 'job': job})


# ──────────────────────────────────────────────────────────────────────────────
# Job Detail
# ──────────────────────────────────────────────────────────────────────────────
@login_required
def job_detail(request, pk):
    """Show details of a scrape job and recent results."""
    job = get_object_or_404(ScrapeJob, pk=pk, user=request.user)
    results_qs = job.results.order_by('element_index')
    paginator = Paginator(results_qs, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    return render(request, 'scraper/job_detail.html', {'job': job, 'page_obj': page_obj})


# ──────────────────────────────────────────────────────────────────────────────
# Run Job (synchronous)
# ──────────────────────────────────────────────────────────────────────────────
@login_required
@require_POST
def job_run(request, pk):
    """Trigger a scrape job synchronously and store results."""
    job = get_object_or_404(ScrapeJob, pk=pk, user=request.user)

    if job.status == 'running':
        messages.warning(request, 'Job is already running.')
        return redirect('job_detail', pk=pk)

    # Mark job as running
    job.status = 'running'
    job.error_message = ''
    job.save(update_fields=['status', 'error_message'])

    try:
        result = scrape_url(
            url=job.url,
            css_selector=job.css_selector,
            extract_attribute=job.extract_attribute or 'text',
            extra_headers=job.get_headers_dict(),
        )

        # Clear old results before storing new ones
        job.results.all().delete()

        if result.success and result.elements:
            ScrapeResult.objects.bulk_create([
                ScrapeResult(
                    job=job,
                    content=el.content,
                    element_tag=el.tag,
                    element_index=el.index,
                )
                for el in result.elements
            ])
            job.status = 'done'
            job.error_message = result.error  # may contain "no elements matched" note
            messages.success(
                request,
                f'Scraped {len(result.elements)} element(s) successfully!'
            )
        elif result.success and not result.elements:
            job.status = 'done'
            job.error_message = result.error or 'No elements matched the selector.'
            messages.warning(request, job.error_message)
        else:
            job.status = 'failed'
            job.error_message = result.error
            messages.error(request, f'Scraping failed: {result.error}')

    except Exception as exc:
        logger.exception("Unexpected error running job %s", pk)
        job.status = 'failed'
        job.error_message = f'Unexpected error: {exc}'
        messages.error(request, f'Unexpected error: {exc}')

    finally:
        job.last_run_at = django_timezone.now()
        job.save(update_fields=['status', 'error_message', 'last_run_at'])

    return redirect('job_detail', pk=pk)


# ──────────────────────────────────────────────────────────────────────────────
# Delete Job
# ──────────────────────────────────────────────────────────────────────────────
@login_required
@require_POST
def job_delete(request, pk):
    """Delete a scrape job and all its results."""
    job = get_object_or_404(ScrapeJob, pk=pk, user=request.user)
    name = job.name
    job.delete()
    messages.success(request, f'Job "{name}" deleted.')
    return redirect('dashboard')


# ──────────────────────────────────────────────────────────────────────────────
# Clear Results
# ──────────────────────────────────────────────────────────────────────────────
@login_required
@require_POST
def job_clear_results(request, pk):
    """Clear all results for a job without deleting the job itself."""
    job = get_object_or_404(ScrapeJob, pk=pk, user=request.user)
    count = job.results.count()
    job.results.all().delete()
    job.status = 'idle'
    job.save(update_fields=['status'])
    messages.info(request, f'Cleared {count} result(s).')
    return redirect('job_detail', pk=pk)


# ──────────────────────────────────────────────────────────────────────────────
# Export Results — CSV
# ──────────────────────────────────────────────────────────────────────────────
@login_required
def export_csv(request, pk):
    """Download all results for a job as a CSV file."""
    job = get_object_or_404(ScrapeJob, pk=pk, user=request.user)
    results = job.results.order_by('element_index')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{job.name}_results.csv"'

    writer = csv.writer(response)
    writer.writerow(['#', 'Tag', 'Content', 'Scraped At'])
    for r in results:
        writer.writerow([r.element_index, r.element_tag, r.content, r.scraped_at.strftime('%Y-%m-%d %H:%M:%S')])

    return response


# ──────────────────────────────────────────────────────────────────────────────
# Export Results — JSON
# ──────────────────────────────────────────────────────────────────────────────
@login_required
def export_json(request, pk):
    """Download all results for a job as a JSON file."""
    job = get_object_or_404(ScrapeJob, pk=pk, user=request.user)
    results = job.results.order_by('element_index')

    data = {
        'job': {
            'id': job.pk,
            'name': job.name,
            'url': job.url,
            'css_selector': job.css_selector,
            'last_run_at': job.last_run_at.isoformat() if job.last_run_at else None,
        },
        'results': [
            {
                'index': r.element_index,
                'tag': r.element_tag,
                'content': r.content,
                'scraped_at': r.scraped_at.isoformat(),
            }
            for r in results
        ],
    }

    response = HttpResponse(
        json.dumps(data, indent=2, ensure_ascii=False),
        content_type='application/json',
    )
    response['Content-Disposition'] = f'attachment; filename="{job.name}_results.json"'
    return response


# ──────────────────────────────────────────────────────────────────────────────
# Job Status (AJAX polling)
# ──────────────────────────────────────────────────────────────────────────────
@login_required
def job_status_api(request, pk):
    """Return job status as JSON — used by the frontend for live polling."""
    job = get_object_or_404(ScrapeJob, pk=pk, user=request.user)
    return JsonResponse({
        'status': job.status,
        'badge_class': job.status_badge_class,
        'result_count': job.result_count,
        'last_run_at': job.last_run_at.strftime('%Y-%m-%d %H:%M:%S') if job.last_run_at else None,
    })
