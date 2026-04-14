"""
Send a dummy weather alert SMS/WhatsApp to a phone number to verify Twilio is wired up.

Usage:
  python scripts/send_test_sms.py --phone +919876543210
  python scripts/send_test_sms.py --phone +919876543210 --channel whatsapp
  python scripts/send_test_sms.py --phone +919876543210 --channel both
  python scripts/send_test_sms.py --phone +919876543210 --dry-run   # print only, no send
"""

import argparse
import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_SMS_FROM, TWILIO_WHATSAPP_FROM

# ── Dummy alert messages in each language ────────────────────────────────────
DUMMY_ALERTS = {
    "english": (
        "🌾 TEST ALERT | Pune, Maharashtra\n"
        "Heatwave warning: Max temp 41°C on Apr 14 & 16.\n"
        "Cover sugarcane with mulch. Give extra water to cattle before 8am.\n"
        "Avoid spraying pesticides. Stay safe! – IMD Weather Alert"
    ),
    "hindi": (
        "🌾 परीक्षण अलर्ट | पुणे, महाराष्ट्र\n"
        "लू की चेतावनी: 14 और 16 अप्रैल को अधिकतम तापमान 41°C।\n"
        "गन्ना और प्याज: सुबह जल्दी पानी दें, मल्च लगाएं। मवेशियों को\n"
        "छाया में रखें। कीटनाशक न करें। – IMD मौसम अलर्ट"
    ),
    "marathi": (
        "🌾 चाचणी इशारा | पुणे, महाराष्ट्र\n"
        "उष्णतेची लाट: १४ व १६ एप्रिल रोजी कमाल तापमान ४१°C.\n"
        "ऊस व कांदा: पहाटे पाणी द्या, मल्च घाला. जनावरांना सावलीत ठेवा.\n"
        "कीटकनाशक फवारणी टाळा. काळजी घ्या! – IMD हवामान इशारा"
    ),
    "telugu": (
        "🌾 పరీక్ష హెచ్చరిక | పూణే, మహారాష్ట్ర\n"
        "వేడి వేవ్ హెచ్చరిక: ఏప్రిల్ 14 & 16న గరిష్ట 41°C।\n"
        "చెరకుపై మల్చ్ వేయండి. ఉదయం 8 గంటలలోపు పశువులకు నీరు ఇవ్వండి.\n"
        "పురుగుమందులు చల్లకండి. జాగ్రత్తగా ఉండండి! – IMD వాతావరణ హెచ్చరిక"
    ),
    "kannada": (
        "🌾 ಪರೀಕ್ಷಾ ಎಚ್ಚರಿಕೆ | ಪುಣೆ, ಮಹಾರಾಷ್ಟ್ರ\n"
        "ಶಾಖ ತರಂಗ ಎಚ್ಚರಿಕೆ: ಏಪ್ರಿಲ್ 14 & 16ರಂದು ಗರಿಷ್ಠ 41°C.\n"
        "ಕಬ್ಬು ಮತ್ತು ಈರುಳ್ಳಿಗೆ ಮಲ್ಚ್ ಹಾಕಿ, ಬೆಳಿಗ್ಗೆ ನೀರು ಕೊಡಿ. ಜಾನುವಾರುಗಳನ್ನು\n"
        "ನೆರಳಿನಲ್ಲಿ ಇರಿಸಿ. ಕೀಟನಾಶಕ ಸಿಂಪಡಿಸಬೇಡಿ. – IMD ಹವಾಮಾನ ಎಚ್ಚರಿಕೆ"
    ),
    "punjabi": (
        "🌾 ਟੈਸਟ ਅਲਰਟ | ਪੁਣੇ, ਮਹਾਰਾਸ਼ਟਰ\n"
        "ਲੂ ਦੀ ਚੇਤਾਵਨੀ: 14 ਅਤੇ 16 ਅਪ੍ਰੈਲ ਨੂੰ ਵੱਧ ਤੋਂ ਵੱਧ 41°C.\n"
        "ਗੰਨਾ ਅਤੇ ਪਿਆਜ਼: ਸਵੇਰੇ ਜਲਦੀ ਪਾਣੀ ਦਿਓ, ਮਲਚ ਲਗਾਓ। ਪਸ਼ੂਆਂ ਨੂੰ\n"
        "ਛਾਂ ਵਿੱਚ ਰੱਖੋ। – IMD ਮੌਸਮ ਅਲਰਟ"
    ),
}


def _creds_configured() -> bool:
    placeholder = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    return bool(
        TWILIO_ACCOUNT_SID
        and TWILIO_ACCOUNT_SID != placeholder
        and TWILIO_AUTH_TOKEN
        and TWILIO_SMS_FROM
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a test SMS/WhatsApp alert")
    parser.add_argument("--phone", required=True, help="Recipient E.164 phone, e.g. +919876543210")
    parser.add_argument(
        "--channel", choices=["sms", "whatsapp", "both"], default="sms",
        help="Delivery channel (default: sms)"
    )
    parser.add_argument(
        "--language", choices=list(DUMMY_ALERTS.keys()), default="marathi",
        help="Language of the dummy alert (default: marathi)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print the message without actually sending"
    )
    args = parser.parse_args()

    message = DUMMY_ALERTS[args.language]
    today = date.today().strftime("%d %b %Y")

    print(f"\n{'='*60}")
    print(f"Test Alert  |  {today}  |  {args.language.title()}")
    print(f"To          :  {args.phone}")
    print(f"Channel     :  {args.channel}")
    print(f"{'='*60}")
    print(f"\nMessage:\n{message}\n")

    if args.dry_run:
        print("[DRY-RUN] Message printed above — NOT sent.")
        return

    if not _creds_configured():
        print(
            "⚠  Twilio credentials are not configured in .env\n"
            "   Edit .env and set:\n"
            "     TWILIO_ACCOUNT_SID=AC...\n"
            "     TWILIO_AUTH_TOKEN=...\n"
            "     TWILIO_SMS_FROM=+1...\n"
            "     TWILIO_WHATSAPP_FROM=whatsapp:+1...\n\n"
            "   Until then, use --dry-run to preview alerts without sending."
        )
        sys.exit(1)

    from src.notifier import dispatch_alert
    result = dispatch_alert(to_phone=args.phone, message=message, channel=args.channel)

    if result["errors"]:
        print(f"✗ Failed: {result['errors']}")
        sys.exit(1)

    if result["sms"]:
        print(f"✓ SMS sent  — SID: {result['sms']}")
    if result["whatsapp"]:
        print(f"✓ WhatsApp  — SID: {result['whatsapp']}")


if __name__ == "__main__":
    main()
