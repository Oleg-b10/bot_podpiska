from pydantic import BaseModel

class Features(BaseModel):
    faq: bool = True
    ai_chat: bool = False
    feedback: bool = True
    
    lead_capture: bool = True          # ← будем делать первым
    lead_to_sheets: bool = True        # запись в Google Sheets
    lead_notify_manager: bool = True   # уведомление в ЛС
    
    segmentation: bool = False
    funnel: bool = False
    mailing: bool = False
    shop: bool = False
    payments_yookassa: bool = False
    payments_crypto: bool = False
    referral: bool = False
    edo: bool = False
    analytics: bool = False
    admin_panel: bool = True

features = Features()
