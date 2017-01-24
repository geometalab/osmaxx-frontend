from django.contrib.auth import get_user_model

from osmaxx.excerptexport.models import ExtractionOrder, Excerpt
from osmaxx.utilities.shortcuts import Emissary

from hamcrest import contains_string, match_equality


def test_send_email_if_all_exports_done_keeps_special_characters_unescaped(mocker, rf):
    User = get_user_model()  # noqa
    extraction_order = ExtractionOrder(orderer=User(), excerpt=Excerpt(name='foo & bar'))
    incoming_request = rf.get('')
    im = mocker.patch.object(Emissary, 'inform_mail')

    extraction_order.send_email_if_all_exports_done(incoming_request)

    im.assert_called_once_with(
        subject=match_equality(contains_string('foo & bar')),
        mail_body=match_equality(contains_string('foo & bar')),
    )
