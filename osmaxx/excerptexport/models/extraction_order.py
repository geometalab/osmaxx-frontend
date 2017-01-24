from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from osmaxx.conversion.converters.detail_levels import DETAIL_LEVEL_CHOICES, DETAIL_LEVEL_ALL
from osmaxx.conversion_api import coordinate_reference_systems as crs
from .excerpt import Excerpt


class ExtractionOrder(models.Model):
    coordinate_reference_system = models.IntegerField(
        verbose_name=_('CRS'), choices=crs.CRS_CHOICES, default=crs.WGS_84
    )
    detail_level = models.IntegerField(
        verbose_name=_('detail level'), choices=DETAIL_LEVEL_CHOICES, default=DETAIL_LEVEL_ALL
    )
    process_id = models.TextField(blank=True, null=True, verbose_name=_('process link'))
    orderer = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='extraction_orders', verbose_name=_('orderer'))
    excerpt = models.ForeignKey(Excerpt, related_name='extraction_orders', verbose_name=_('excerpt'), null=True)
    progress_url = models.URLField(verbose_name=_('progress URL'), null=True, blank=True)

    def forward_to_conversion_service(self, *, incoming_request):
        clipping_area_json = self.excerpt.send_to_conversion_service()
        jobs_json = [
            export.send_to_conversion_service(clipping_area_json, incoming_request)
            for export in self.exports.all()
        ]
        return jobs_json

    def __str__(self):
        return ', '.join(
            [
                '[{order_id}] orderer: {orderer_name}'.format(
                    order_id=self.id,
                    orderer_name=self.orderer.get_username(),
                ),
                'excerpt: {}'.format(str(self.excerpt_name)),
            ]
        )

    @property
    def excerpt_name(self):
        """
        Returns:
              user-given excerpt name for user-defined excerpts,
              country name for countries,
              None if order has no excerpt (neither country nor user-defined)
        """
        if self.excerpt:
            return self.excerpt.name

    @property
    def extraction_formats(self):
        return self.exports.values_list('file_format', flat=True)

    @extraction_formats.setter
    def extraction_formats(self, value):
        new_formats = frozenset(value)
        previous_formats = self.exports.values_list('file_format', flat=True)
        assert new_formats.issuperset(previous_formats)
        self._new_formats = new_formats  # Will be collected and cleaned up by attach_new_formats.
        if self.id is not None:
            attach_new_formats(self.__class__, instance=self)

    def get_absolute_url(self):
        from django.core.urlresolvers import reverse
        return reverse('excerptexport:export_list')

    def send_email_if_all_exports_done(self, incoming_request):
        if all(export.is_status_final for export in self.exports.all()):
            from osmaxx.utilities.shortcuts import Emissary
            emissary = Emissary(recipient=self.orderer)
            emissary.inform_mail(
                subject=self._get_all_exports_done_email_subject(),
                mail_body=self._get_all_exports_done_mail_body(incoming_request)
            )

    def _get_all_exports_done_email_subject(self):
        view_context = dict(
            extraction_order=self,
            successful_exports_count=self.exports.filter(output_file__isnull=False).count(),
            failed_exports_count=self.exports.filter(output_file__isnull=True).count(),
        )
        return render_to_string(
            'excerptexport/email/all_exports_of_extraction_order_done_subject.txt',
            context=view_context,
            using='plaintext',
        ).strip()

    def _get_all_exports_done_mail_body(self, incoming_request):
        view_context = dict(
            extraction_order=self,
            successful_exports=self.exports.filter(output_file__isnull=False),
            failed_exports=self.exports.filter(output_file__isnull=True),
            request=incoming_request,
        )
        return render_to_string(
            'excerptexport/email/all_exports_of_extraction_order_done_body.txt',
            context=view_context,
            using='plaintext',
        ).strip()


@receiver(post_save, sender=ExtractionOrder)
def attach_new_formats(sender, instance, **kwargs):
    if hasattr(instance, '_new_formats'):
        for format in instance._new_formats:
            instance.exports.get_or_create(file_format=format)
        del instance._new_formats
