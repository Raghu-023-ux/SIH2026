from typing import Dict, Any, Optional


class I18nAlertTemplateService:
    """
    Multilingual warning template generator for North Eastern Region linguistic communities.
    Provides localized SMS (<= 160 chars) and WhatsApp messages in English, Hindi, Assamese, Bengali, and Mizo.
    """

    @staticmethod
    def get_sms_translations(
        district: str,
        state: str,
        severity: str
    ) -> Dict[str, str]:
        # 1. English
        sms_en = f"ALERT: {severity} Landslide Risk in {district}. Move away from steep slopes & blocked roads. Guidance: sih.gov.in/p Helplines:112/1070"
        if len(sms_en) > 160:
            sms_en = f"ALERT: {severity} Landslide Risk in {district}. Move to safe ground. Helplines:112/1070"

        # 2. Hindi
        sms_hi = f"चेतावनी: {district} में भूस्खलन का {severity} खतरा। ढलानों व अवरुद्ध सड़कों से दूर रहें। हेल्पलाइन: 112/1070"

        # 3. Assamese (for Assam / Dima Hasao)
        sms_as = f"সতর্কতা: {district} জিলাত ভূমিস্খলনৰ {severity} আশংকা। বিপদজনক পাহাৰীয়া ঢালৰ পৰা আঁতৰি থাকক। হেল্পলাইন: ১১২/১০৭০"

        # 4. Bengali
        sms_bn = f"সতর্কবার্তা: {district}-এ মারাত্মক ভূমিধসের সম্ভাবনা। খাড়া ঢাল ও অবরুদ্ধ রাস্তা এড়িয়ে চলুন। হেল্পলাইন: ১১২/১০৭০"

        # 5. Mizo (for Mizoram / Aizawl)
        sms_mizo = f"THUCHUAH: {district}-ah lei min hlauhawm ({severity}) a awm. Hmun hlauhawm leh kawng ping kalsan rawh. Helpline: 112/1070"

        return {
            "en": sms_en,
            "hi": sms_hi,
            "as": sms_as,
            "bn": sms_bn,
            "lus": sms_mizo,
        }

    @staticmethod
    def get_regional_sms(district: str, state: str, severity: str) -> str:
        trans = I18nAlertTemplateService.get_sms_translations(district, state, severity)
        st_upper = state.upper()
        if "MIZORAM" in st_upper:
            return trans["lus"]
        elif "ASSAM" in st_upper:
            return trans["as"]
        elif "TRIPURA" in st_upper:
            return trans["bn"]
        else:
            return trans["hi"]


i18n_templates = I18nAlertTemplateService()
