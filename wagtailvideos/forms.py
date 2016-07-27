from django import forms
from django.forms.models import modelform_factory
from django.utils.translation import ugettext as _
from enumchoicefield.forms import EnumField
from wagtail.wagtailadmin import widgets
from wagtail.wagtailadmin.forms import (BaseCollectionMemberForm,
                                        collection_member_permission_formset_factory)

from wagtailvideos.fields import WagtailVideoField
from wagtailvideos.models import MediaFormats, Video
from wagtailvideos.permissions import \
    permission_policy as video_permission_policy


class BaseVideoForm(BaseCollectionMemberForm):
    permission_policy = video_permission_policy

# Callback to allow us to override the default form field for the image file field
def formfield_for_dbfield(db_field, **kwargs):
    # Check if this is the file field
    if db_field.name == 'file':
        return WagtailVideoField(**kwargs)

    # For all other fields, just call its formfield() method.
    return db_field.formfield(**kwargs)


def get_video_form(model):
    fields = model.admin_form_fields
    if 'collection' not in fields:
        # force addition of the 'collection' field, because leaving it out can
        # cause dubious results when multiple collections exist (e.g adding the
        # document to the root collection where the user may not have permission) -
        # and when only one collection exists, it will get hidden anyway.
        print('collection not found')
        fields = list(fields) + ['collection']

    return modelform_factory(
        model,
        form=BaseVideoForm,
        fields=fields,
        formfield_callback=formfield_for_dbfield,
        # set the 'file' widget to a FileInput rather than the default ClearableFileInput
        # so that when editing, we don't get the 'currently: ...' banner which is
        # a bit pointless here
        widgets={
            'tags': widgets.AdminTagWidget,
            'file': forms.FileInput(),
        })


class VideoTranscodeAdminForm(forms.Form):
    media_format = EnumField(MediaFormats)

    def __init__(self, data=None, *, video, **kwargs):
        super().__init__(**kwargs, data=None)
        self.video = video

    def save(self):
        media_format = self.cleaned_data['media_format']
        self.video.do_transcode(media_format)


GroupVideoPermissionFormSet = collection_member_permission_formset_factory(
    Video,
    [
        ('add_video', _("Add"), _("Add/edit images you own")),
        ('change_video', _("Edit"), _("Edit any video")),
    ],
    'wagtailvideos/permissions/includes/video_permissions_formset.html'
)
