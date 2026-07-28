"""
Generate massively expanded comprehensive test cases CSV.
Covers the chaotic diversity of real Indian user inputs across 60+ categories.
"""

import csv
import os

HEADER = [
    "test_id", "language", "scenario_type",
    "input_message", "expected_keywords",
    "expected_classification", "expected_journey", "notes",
]

# ── Helper ──────────────────────────────────────────────────────────
next_id_counter = [701]  # start after existing 700-ish

def tc_id(prefix: str) -> str:
    next_id_counter[0] += 1
    return f"{prefix}_{next_id_counter[0]:03d}"

# ── New sections ────────────────────────────────────────────────────

cases = []

# =====================================================================
# SECTION 31: ROMANIZED HINDI / PURE HINGLISH (the way India actually types)
# =====================================================================
hinglish_cases = [
    ("hing", "Mere account se paisa nikal gaya koi hack kar liya", "paise|account|hack|help"),
    ("hing", "Kisine mera UPI hack kar liya hai kya karun", "upi|hack|help|recovery"),
    ("hing", "Maine kisi ko OTP bata diya ab kya hoga", "otp|bata|diya|recovery"),
    ("hing", "Ek call aaya tha bank se bol rahe the account block", "call|bank|account|scam"),
    ("hing", "Google pay mein paise nahi aa rahe transfer kiye the", "gpay|paise|transfer|recovery"),
    ("hing", "PhonePe se paise gaye kisine aur use kar liye", "phonepe|paise|fraud|recovery"),
    ("hing", "QR code scan kiya socha paise aayenge ulta gaye", "qr|scan|paise|scam"),
    ("hing", "Mera WhatsApp hack ho gaya hai kya karun batao", "whatsapp|hack|help"),
    ("hing", "Bank ne kaha account mein problem hai OTP do", "bank|otp|scam|fraud"),
    ("hing", "Police ne video call kiya bol rahe humare naam case hai", "police|video|call|digital|arrest"),
    ("hing", "Link pe click kiya aur details daal di phir pachtaya", "link|click|details|phishing"),
    ("hing", "AnyDesk install kar liya unhone phone control kiya", "anydesk|remote|control|scam"),
    ("hing", "Mera SIM band ho gaya aur bank account empty ho gaya", "sim|band|account|recovery"),
    ("hing", "Job ka offer aaya tha registration fee maang rahe hain", "job|registration|fee|scam"),
    ("hing", "Coin me paise lagaye ab nikal nahi pa raha hoon", "coin|crypto|investment|recovery"),
    ("hing", "Aadhaar card kisi ne use kar liya loan nikal liya", "aadhaar|loan|identity|theft"),
    ("hing", "Koi muje blackmail kar raha hai mere photo leak karne ki dhamki", "blackmail|photo|leak|help"),
    ("hing", "Bhai please help mera account saaf kar diya fraud ne", "bhai|help|account|fraud|recovery"),
    ("hing", "Maine OLX par mobile becha tha buyer ne QR bheja", "olx|qr|buyer|marketplace"),
    ("hing", "Call aaya Microsoft se bola computer mein virus hai", "microsoft|virus|tech|support|scam"),
    ("hing", "Mujhe koi phone kiya aur OTP puch liya maine de diya", "otp|phone|call|scam"),
    ("hing", "Petrol pump par QR scan karwaya paise kat gaye", "qr|petrol|scan|scam"),
    ("hing", "Bina bataye mere account se paise cut rahe hain", "account|paise|unauthorized|fraud"),
    ("hing", "Koi mera number use kar ke loan app se paise nikal raha hai", "loan|app|identity|theft"),
    ("hing", "Mere ghar pe koi aaya policy renewal ke liye paise liye", "policy|insurance|renewal|scam"),
    ("hing", "Electricity bill ka discount ka link aaya hai", "electricity|bill|link|phishing"),
    ("hing", "FASTag recharge ka message aaya link ke saath", "fastag|recharge|link|phishing"),
    ("hing", "PM Kisan Yojana ke naam pe paise ka offer aaya", "pm|kisan|scheme|scam"),
    ("hing", "Koi WhatsApp group mein invest karo 2000 se 50000 banao", "whatsapp|invest|group|scam"),
    ("hing", "Mera Facebook kisi ne hack kar liya password change kar diya", "facebook|hack|password|account"),
]
for lang, msg, kw in hinglish_cases:
    uid = tc_id("TC_HING")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"Hinglish: {msg[:40]}"])

# =====================================================================
# SECTION 32: PANICKED / DISTRESSED TYPING (ALL CAPS, repeating, urgent)
# =====================================================================
panic_cases = [
    ("en", "HELP HELP HELP SOMEONE TOOK ALL MY MONEY WHAT DO I DO", "help|urgent|money|recovery"),
    ("en", "PLEASE PLEASE PLEASE HELP ME I AM BEING SCAMMED RIGHT NOW", "help|urgent|scam|immediate"),
    ("en", "WHAT SHOULD I DO WHAT SHOULD I DO MY ACCOUNT IS EMPTY", "account|empty|help|recovery"),
    ("en", "I AM PANICKING SOMEONE PLEASE TELL ME WHAT TO DO NOW", "panic|help|recovery"),
    ("en", "BHAI BHAI BHAI ACCOUNT SE PAISE CUT GAYE BINA PUCHHE", "paise|account|help|recovery"),
    ("en", "SIR SIR SIR PLEASE HELP MERE SAATH SCAM HUA HAI", "sir|help|scam|recovery"),
    ("en", "OMG OMG OMG THEY TOOK EVERYTHING I AM SHAKING", "help|everything|scam|recovery"),
    ("hing", "Kya karun kya karun kya karun koi batado please", "help|kya|karun|recovery"),
    ("hing", "Mera toh pura savings khatam ho gaya please help", "savings|khatam|help|recovery"),
    ("hing", "PLEASE SIR MERI HELP KARO MUJHE NAHI PATHA KYA KARUN", "help|sir|recovery|scam"),
    ("en", "This just happened 5 minutes ago what do I do immediately", "urgent|just|happened|help"),
    ("en", "It is happening right now they are on the phone with me", "happening|right|now|help"),
    ("en", "I am on call with them please tell me what to do quickly", "urgent|help|quick|recovery"),
    ("en", "They are still messaging me what should I say to them", "messaging|help|scam|preventive"),
    ("en", "I just gave them my OTP 30 seconds ago can I stop it", "otp|just|gave|urgent|recovery"),
]
for lang, msg, kw in panic_cases:
    uid = tc_id("TC_PANIC")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"Panicked: {msg[:50]}"])

# =====================================================================
# SECTION 33: INDIAN ENGLISH VARIATIONS
# =====================================================================
indeng_cases = [
    ("en", "Myself Ramesh I am having a problem with my bank account only", "problem|bank|account|help"),
    ("en", "Kindly do the needful as my money has been taken", "kindly|needful|money|recovery"),
    ("en", "Do one thing just block my account immediately only", "block|account|immediate"),
    ("en", "Please revert at the earliest my account is hacked", "revert|account|hack|help"),
    ("en", "I am having one issue someone took my OTP", "issue|otp|scam"),
    ("en", "Sir kindly look into this matter I lost my money", "sir|money|lost|recovery"),
    ("en", "This is urgent kindly tell me what to do now itself", "urgent|kindly|help|recovery"),
    ("en", "I am not having any idea what is happening to my account", "account|help|fraud|hack"),
    ("en", "They only were calling me again and again I got scared", "calling|scam|help"),
    ("en", "I wanted to ask whether this message is genuine or fake", "message|genuine|fake|scam"),
    ("en", "I am doing online transaction only suddenly money gone", "transaction|money|gone|upi"),
    ("en", "Is there any solution for my problem please tell na", "solution|help|recovery|scam"),
    ("en", "What to do yaar someone made fool of me", "fool|scam|help|recovery"),
    ("en", "I will be thankful if you kindly help me in this matter", "thankful|help|recovery|scam"),
    ("en", "I have a small doubt is this genuine or scam please check", "doubt|genuine|scam|check"),
]
for lang, msg, kw in indeng_cases:
    uid = tc_id("TC_INDENG")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"Indian English: {msg[:50]}"])

# =====================================================================
# SECTION 34: DEEPFAKE / AI VOICE SCAMS (modern threats)
# =====================================================================
deepfake_cases = [
    ("en", "My friend called me saying I am in trouble but it was an AI voice of me", "ai|voice|deepfake|scam"),
    ("en", "Someone used AI to clone my voice and called my mother for money", "ai|voice|clone|scam"),
    ("en", "I received a video call but the person's face looked fake like AI", "ai|video|deepfake|face"),
    ("en", "They sent me a recording of my voice that I never said AI generated", "voice|recording|ai|blackmail"),
    ("en", "My photo was used to create a fake video now they are blackmailing", "fake|video|ai|blackmail|sextortion"),
    ("en", "Someone made a deepfake of me and posted on social media", "deepfake|social|media|scam"),
    ("en", "I got a call from my boss asking for money but it was AI voice", "ai|voice|boss|fraud"),
    ("en", "They used my WhatsApp voice note and created something fake", "whatsapp|voice|fake|ai"),
    ("en", "A stranger sent me a very realistic video of myself from my photos", "video|deepfake|photos|blackmail"),
    ("en", "Someone cloned my father's voice and called me for emergency money", "voice|clone|emergency|scam"),
]
for lang, msg, kw in deepfake_cases:
    uid = tc_id("TC_AI")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"AI/Deepfake: {msg[:50]}"])

# =====================================================================
# SECTION 35: COURIER / PARCEL SCAMS
# =====================================================================
courier_cases = [
    ("en", "I got a call from FedEx saying a parcel has been seized by NCB with drugs", "courier|parcel|ncb|drugs"),
    ("en", "DHL ka message aaya parcel custom mein phans gaya hai paise do", "dhl|custom|parcel|scam"),
    ("en", "India Post ne SMS bheja parcel deliver nahi hua click karo", "india|post|parcel|link|phishing"),
    ("en", "A courier company called saying my parcel contains illegal items", "courier|illegal|parcel|drugs|scam"),
    ("en", "Blue Dart se message aaya parcel weight zyada hai extra pay karo", "bluedart|parcel|extra|payment"),
    ("en", "Ek parcel aaya tha USA se jiska maine order nahi kiya ab charges maang rahe", "parcel|usa|charges|scam"),
    ("en", "Amazon delivery driver called saying address is wrong send OTP for verification", "amazon|delivery|otp|scam"),
    ("en", "I got a missed call from international number and now parcel scam calls started", "missed|call|international|parcel"),
    ("en", "DTDC walo ne kaha parcel deliver karna hai extra shipping charges bharein", "dtdc|parcel|shipping|charges"),
    ("en", "Customs clearance ke liye paise maang rahe hain parcel ka", "customs|clearance|parcel|scam"),
]
for lang, msg, kw in courier_cases:
    uid = tc_id("TC_COURIER")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"Courier: {msg[:50]}"])

# =====================================================================
# SECTION 36: FASTag / TOLL SCAMS
# =====================================================================
fastag_cases = [
    ("en", "FASTag recharge failed message aaya link pe click karo", "fastag|recharge|link|phishing"),
    ("en", "Your FASTag is deactivated update KYC fastag-update.com", "fastag|kyc|deactivated|scam"),
    ("en", "FASTag balance low recharge now before toll penalty link given", "fastag|balance|recharge|link"),
    ("en", "NHAI ne message bheja FASTag block ho jayega click karo", "nhai|fastag|block|phishing"),
    ("en", "Mera FASTag ka paisa double cut ho gaya kya karun", "fastag|double|debit|recovery"),
    ("en", "I got a fake FASTag customer care number from Google and paid them", "fastag|customer|care|fake|scam"),
    ("en", "Toll plaza pe QR code tha scan karo FASTag recharge karo fraud ho gaya", "toll|qr|fastag|recharge"),
    ("en", "Someone sent me FASTag payment link that looked like NPCI", "fastag|payment|link|npci"),
    ("en", "I tried to recharge FASTag through a third party website money deducted no recharge", "fastag|recharge|thirdparty|fraud"),
    ("en", "Message aaya FASTag KYC pending update karo warna block", "fastag|kyc|pending|phishing"),
]
for lang, msg, kw in fastag_cases:
    uid = tc_id("TC_FASTAG")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"FASTag: {msg[:50]}"])

# =====================================================================
# SECTION 37: GOVERNMENT SCHEME SCAMS
# =====================================================================
govt_cases = [
    ("en", "PM Kisan Samman Nidhi ke naam pe SMS aaya hai link ke saath", "pm|kisan|scheme|link|phishing"),
    ("en", "Ayushman Bharat card free mein bana rahe hain Aadhaar do", "ayushman|bharat|card|aadhaar"),
    ("en", "MGNREGA payment pending hai link click karo form bharo", "mgnrega|payment|link|scam"),
    ("en", "PM Awas Yojana subsidy aapko mil rahi hai registration fee bharein", "pm|awas|subsidy|fee|scam"),
    ("en", "Sarkari scholarship mil rahi hai processing fee bharein", "scholarship|govt|fee|scam"),
    ("en", "Ration card update ka message aaya Aadhaar link karo", "ration|card|aadhaar|link|phishing"),
    ("en", "Pension scheme mein registration karaiye first month free", "pension|scheme|registration|scam"),
    ("en", "Jal Jeevan Mission ke naam pe paise mang rahe hain", "jal|jeevan|mission|scam"),
    ("en", "SBI pensioners ke liye special update KYC link aaya hai", "pension|kyc|sbi|link|phishing"),
    ("en", "EPFO claim pending hai link se verify karo", "epfo|claim|pending|link|phishing"),
    ("en", "Aadhaar-PAN link nahi kiya to block ho jayega link click karo", "aadhaar|pan|link|block|phishing"),
    ("en", "Income tax refund aapko mil rahi hai form bharo link mein", "income|tax|refund|link|phishing"),
    ("en", "GST refund pending hai verify karo bank details update karo", "gst|refund|verify|scam"),
    ("en", "Sarkari naukri ke liye registration form bharo fee maang rahe", "sarkari|naukri|registration|fee"),
    ("en", "Caste certificate banwao online scam hai kya", "caste|certificate|online|scam"),
]
for lang, msg, kw in govt_cases:
    uid = tc_id("TC_GOVT")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"Govt Scheme: {msg[:50]}"])

# =====================================================================
# SECTION 38: UTILITY BILL SCAMS
# =====================================================================
bill_cases = [
    ("en", "Bijli bill 50% discount ka offer aaya link ke saath", "bijli|bill|discount|link|scam"),
    ("en", "Your electricity bill payment failed click here to retry", "electricity|bill|payment|link|phishing"),
    ("en", "Gas cylinder booking confirm karo advance payment karo", "gas|cylinder|booking|advance|scam"),
    ("en", "Pani ka bill pending hai online pay karo warna cut ho jayega", "pani|bill|pending|scam"),
    ("en", "Broadband bill autopay failed update card details", "broadband|bill|autopay|scam"),
    ("en", "I paid my water bill through a link on WhatsApp now money gone", "bill|payment|whatsapp|link|scam"),
    ("en", "Electricity board se message aaya meter change karna hai online pay karo", "meter|change|electricity|scam"),
    ("en", "LPG gas subsidy aapko mil rahi hai bank details update karo", "lpg|subsidy|bank|details|scam"),
    ("en", "Piped gas connection new booking fee online pay karo", "piped|gas|booking|fee|scam"),
    ("en", "I got a call from KESCO asking for bill payment through UPI", "kesco|bill|upi|payment"),
]
for lang, msg, kw in bill_cases:
    uid = tc_id("TC_BILL")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"Bill Scam: {msg[:50]}"])

# =====================================================================
# SECTION 39: TELECOM / SIM CARD SCAMS
# =====================================================================
telecom_cases = [
    ("en", "Your Jio number will be deactivated immediately send OTP to continue", "jio|deactivated|otp|scam"),
    ("en", "Airtel free recharge 4999 claim karo link click karo", "airtel|free|recharge|link|scam"),
    ("en", "VI ne message bheja SIM upgrade karna hai KYC karo", "vi|sim|kyc|upgrade|scam"),
    ("en", "Free JioFiber connection installation only 999 processing fee", "jio|fiber|processing|fee|scam"),
    ("en", "Your number will be traced for illegal activity call now to avoid block", "number|traced|illegal|scam"),
    ("en", "BSNL SIM swap online apply link kaunsa hai", "bsnl|sim|swap|scam"),
    ("en", "I got a call from TRAI saying my number is used for spam", "trai|spam|number|scam"),
    ("en", "Airtel black you have won iPhone 15 click to claim", "airtel|black|iphone|prize|scam"),
    ("en", "Jio 5G upgrade free link pe click karo", "jio|5g|upgrade|link|scam"),
    ("en", "Mera SIM expire ho jayega KYC nahi kiya to link karo", "sim|expire|kyc|link|phishing"),
]
for lang, msg, kw in telecom_cases:
    uid = tc_id("TC_TELECOM")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"Telecom: {msg[:50]}"])

# =====================================================================
# SECTION 40: MATRIMONY / DATING SCAMS
# =====================================================================
matrimony_cases = [
    ("en", "I met someone on Shaadi.com and now they are asking for money", "shaadi|matrimony|money|scam"),
    ("en", "A profile on Jeevansathi keeps asking for gift cards", "jeevansathi|gift|card|scam"),
    ("en", "I talked to a girl on a dating app now she needs emergency money", "dating|emergency|money|scam"),
    ("en", "Someone on matrimonial site wants to send me a parcel need custom fee", "matrimony|parcel|custom|fee|scam"),
    ("en", "US-based NRI ladki hai shaadi ke liye paise mang rahi visa ke", "nri|shaadi|visa|fee|scam"),
    ("en", "I transferred money to my online girlfriend but she never meets me", "girlfriend|money|transfer|dating|scam"),
    ("en", "Matrimony profile verification ke liye OTP maang rahe hain", "matrimony|verification|otp|scam"),
    ("en", "Someone on Tinder said they like me and asked for my bank details", "tinder|bank|details|scam"),
    ("en", "I met someone on Instagram now they say they love me and need money for ticket", "instagram|love|ticket|money|scam"),
    ("en", "A foreigner wants to marry me and is sending a gift need processing fee", "foreigner|gift|processing|fee|scam"),
]
for lang, msg, kw in matrimony_cases:
    uid = tc_id("TC_MATRIMONY")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"Matrimony: {msg[:50]}"])

# =====================================================================
# SECTION 41: REAL ESTATE / PROPERTY SCAMS
# =====================================================================
property_cases = [
    ("en", "I paid token advance for a flat on Housing.com now builder is missing", "flat|advance|builder|missing|scam"),
    ("en", "Property registry ke liye extra paise mang rahe hain agent", "property|registry|agent|fraud"),
    ("en", "Someone is selling land at half market price suspicious", "land|selling|cheap|scam"),
    ("en", "PG owner asking advance for room but not giving keys", "pg|advance|room|scam"),
    ("en", "I found a flat on Nobroker owner asking rent 1 year advance", "nobroker|rent|advance|scam"),
    ("en", "Builder promising 3 BHK at 25 lakhs seems too good to be true", "builder|flat|cheap|scam"),
    ("en", "I booked a villa through an agent now agent not responding", "villa|booking|agent|fraud"),
    ("en", "Property papers mein fraud hua hai registry fake hai", "property|registry|fake|fraud"),
    ("en", "Someone is renting my flat paid extra cheque asking refund of difference", "rental|cheque|refund|overpayment|scam"),
    ("en", "I got a call about investing in Dubai real estate guaranteed returns", "dubai|real|estate|investment|scam"),
]
for lang, msg, kw in property_cases:
    uid = tc_id("TC_PROPERTY")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"Property: {msg[:50]}"])

# =====================================================================
# SECTION 42: EDUCATION / EXAM SCAMS
# =====================================================================
exam_cases = [
    ("en", "I got a message that I passed the exam and need to pay for certificate", "exam|certificate|fee|scam"),
    ("en", "Coaching institute ne refund dena tha nahi diya ab band ho gaye", "coaching|refund|institute|fraud"),
    ("en", "Online course enroll kiya tha 50000 ka ab company gayab", "online|course|enroll|scam"),
    ("en", "NEET rank improve karne ka offer aaya hai paid consultation", "neet|rank|consultation|scam"),
    ("en", "I paid for study abroad consultancy now they are not responding", "study|abroad|consultancy|fraud"),
    ("en", "Competitive exam ka solved paper mil raha hai paise do", "exam|solved|paper|scam"),
    ("en", "Scholarship milne ka SMS aaya hai processing fee bharein", "scholarship|sms|processing|fee|scam"),
    ("en", "University se degree verify karne ka link aaya hai", "university|degree|verify|link|phishing"),
    ("en", "Online exam ka results tamper kar sakte hain paise leke", "exam|results|tamper|fraud"),
    ("en", "PhD admission ke liye donation maang rahe hain college mein", "phd|admission|donation|fraud"),
]
for lang, msg, kw in exam_cases:
    uid = tc_id("TC_EDU")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"Education: {msg[:50]}"])

# =====================================================================
# SECTION 43: MEDICAL / HEALTH SCAMS
# =====================================================================
health_cases = [
    ("en", "Hospital called saying my brother met with accident send money immediately", "hospital|accident|brother|emergency|scam"),
    ("en", "Free health checkup camp mein Aadhaar liya ab fraud ho raha", "health|checkup|aadhaar|scam"),
    ("en", "Corona vaccine ke baad health survey bank details maang rahe", "vaccine|survey|bank|details|scam"),
    ("en", "Ayurvedic medicine guaranteed cure for diabetes click link", "ayurvedic|medicine|cure|link|scam"),
    ("en", "Your medical insurance claim is approved pay processing fee", "medical|insurance|claim|processing|fee"),
    ("en", "Kidney transplant donation ke liye donor mil raha hai paise do", "kidney|donor|transplant|scam"),
    ("en", "Cancer patient donation ka post Facebook pe genuine hai ya fake", "cancer|donation|facebook|scam"),
    ("en", "I ordered medicine from an online pharmacy now they keep calling", "medicine|online|pharmacy|calling|scam"),
    ("en", "Government hospital se free operation ka offer fake lag raha", "hospital|free|operation|scam"),
    ("en", "Vaccine certificate bana lo online without registration", "vaccine|certificate|online|fraud"),
]
for lang, msg, kw in health_cases:
    uid = tc_id("TC_HEALTH")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"Health Scam: {msg[:50]}"])

# =====================================================================
# SECTION 44: CRYPTO / BITCOIN SCAMS (expanded)
# =====================================================================
crypto_cases = [
    ("en", "I invested in Bitcoin through a Telegram group now platform is gone", "bitcoin|telegram|invest|scam"),
    ("en", "Crypto trading app mein paise lagaye ab withdraw nahi ho rahe", "crypto|trading|withdraw|scam"),
    ("en", "Someone promised 10% daily returns on crypto investment", "crypto|daily|returns|ponzi"),
    ("en", "Cloud mining contract liya 1 lakh ka no profit yet", "cloud|mining|contract|scam"),
    ("en", "I bought USDT from a P2P platform now my account frozen", "usdt|p2p|account|frozen|scam"),
    ("en", "NFT invest kiya tha ab koi nahi poochta", "nft|invest|scam"),
    ("en", "Crypto arbitrage bot mein paise laga diye ab system band", "arbitrage|bot|crypto|scam"),
    ("en", "Web3 gaming platform earn karo play karo scam hai kya", "web3|gaming|earn|scam"),
    ("en", "I sent ETH to a fake exchange website now support not responding", "ethereum|exchange|fake|scam"),
    ("en", "Crypto recovery agent ne paise liye recovery nahi kiya", "crypto|recovery|agent|scam"),
]
for lang, msg, kw in crypto_cases:
    uid = tc_id("TC_CRYPTO")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"Crypto: {msg[:50]}"])

# =====================================================================
# SECTION 45: WHATSAPP GROUP / CHANNEL SCAMS
# =====================================================================
whatsapp_scam_cases = [
    ("en", "I was added to a WhatsApp group invest 2000 get 25000 daily profit", "whatsapp|group|invest|scam"),
    ("en", "WhatsApp pe unknown group mein add kiya stock tips de rahe", "whatsapp|stock|tips|scam"),
    ("en", "Koi WhatsApp group mein task de raha hai like YouTube video paise", "whatsapp|task|youtube|scam"),
    ("en", "WhatsApp group admin ban gaya sabke numbers le liye", "whatsapp|group|admin|scam"),
    ("en", "I joined a WhatsApp channel for free tips now they ask for money", "whatsapp|channel|tips|payment"),
    ("en", "Someone created a fake WhatsApp group with my photo and name", "fake|whatsapp|group|identity"),
    ("en", "WhatsApp group mein lottery winner announce kiya fee bharein", "whatsapp|lottery|fee|scam"),
    ("en", "Work from home WhatsApp group mein registration fee maang rahe", "whatsapp|wfh|registration|fee"),
    ("en", "WhatsApp group admin threatening to leak our data if we leave", "whatsapp|threat|data|leak"),
    ("en", "I got a WhatsApp call from an unknown international number", "whatsapp|call|international|scam"),
]
for lang, msg, kw in whatsapp_scam_cases:
    uid = tc_id("TC_WA_SCAM")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"WhatsApp: {msg[:50]}"])

# =====================================================================
# SECTION 46: SOCIAL MEDIA / YOUTUBE / INSTAGRAM SCAMS
# =====================================================================
social_cases = [
    ("en", "YouTube video mein Bitcoin double karne ka scam dekha", "youtube|bitcoin|double|scam"),
    ("en", "Instagram reel mein trading ka ad dekha paise gaye", "instagram|reel|trading|scam"),
    ("en", "Someone commented on my Instagram post offering easy money", "instagram|easy|money|scam"),
    ("en", "YouTube channel hack kar liya kisi ne blackmail kar raha", "youtube|channel|hack|blackmail"),
    ("en", "Instagram pe fake ID bana kar mere friends ko follow request bhej rahe", "instagram|fake|id|identity"),
    ("en", "Telegram channel se trading signal le raha tha sab paise gaye", "telegram|trading|signal|scam"),
    ("en", "YouTube comment mein loan ka ad aaya instant approval", "youtube|loan|instant|approval|scam"),
    ("en", "Instagram influencer ne investment product promote kiya scam", "instagram|influencer|investment|scam"),
    ("en", "Facebook page ne lucky draw winner announce kiya fee bharein", "facebook|lucky|draw|winner|scam"),
    ("en", "Snapchat pe kisi ne blackmail kiya mere private photos le kar", "snapchat|blackmail|photos|sextortion"),
]
for lang, msg, kw in social_cases:
    uid = tc_id("TC_SOCIAL")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"Social Media: {msg[:50]}"])

# =====================================================================
# SECTION 47: TYPING MISTAKE / GIBBERISH VARIATIONS (realistic fat-finger)
# =====================================================================
typo_cases = [
    ("en", "Mai otp bta diya", "otp|scam|help"),
    ("en", "Mere soi ne pocli ce call kee", "police|call|scam|help"),
    ("en", "Somewone tuk my u pi money pls hlp", "upi|money|help|recovery"),
    ("en", "Mane kisi ko aadhar nuer de diya ab kya", "aadhaar|number|misuse|help"),
    ("en", "Neenga help pannunga bro scam aagiduchu", "help|scam|recovery"),
    ("en", "Em account hacked helpme plzzzzz", "account|hack|help|recovery"),
    ("en", "Mera paisa chla gya kya kru", "paisa|gaya|help|recovery"),
    ("en", "Mre mobail m virus aagya ne kya kru", "virus|mobile|help"),
    ("en", "Sim swp ho gyi mre bina jane", "sim|swap|account|recovery"),
    ("en", "Olx p bkia thi kn ne qr bheja", "olx|bike|qr|scam"),
]
for lang, msg, kw in typo_cases:
    uid = tc_id("TC_TYPO")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"Typo: {msg[:40]}"])

# =====================================================================
# SECTION 48: THIRD-PARTY REPORTING (family, friend, elderly)
# =====================================================================
thirdparty_cases = [
    ("en", "My father got a call saying his Aadhaar is blocked what should he do", "father|aadhaar|blocked|scam"),
    ("en", "My mother shared OTP with someone how to help her", "mother|otp|shared|help|recovery"),
    ("en", "My grandmother gave her bank details to a caller what now", "grandmother|bank|details|scam"),
    ("en", "My friend is being blackmailed what should I tell them", "friend|blackmail|help|advice"),
    ("en", "Mere papa ko phone aaya tha account band ho jayega", "papa|phone|account|scam"),
    ("en", "Meri mummy ne OTP bata diya kya karein", "mummy|otp|bata|help"),
    ("en", "My uncle installed AnyDesk on his phone what to do", "uncle|anydesk|remote|help"),
    ("en", "My parents are about to pay for a fake lottery how to stop", "parents|lottery|pay|stop|scam"),
    ("en", "My boss received a fraudulent invoice for payment", "boss|invoice|fraud|payment"),
    ("en", "My sister is talking to someone on dating app asking for money", "sister|dating|money|scam"),
    ("en", "My elderly neighbor is being scammed I want to report", "elderly|neighbor|scam|report"),
    ("en", "Mere chacha ko loan app se threaten kar rahe hain", "chacha|loan|threat|help"),
]
for lang, msg, kw in thirdparty_cases:
    uid = tc_id("TC_3PARTY")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"Third-party: {msg[:50]}"])

# =====================================================================
# SECTION 49: ANGRY / FRUSTRATED USERS
# =====================================================================
angry_cases = [
    ("en", "You people are useless I want my money back now", "money|back|recovery|help"),
    ("en", "Your bot is not helping me I want human agent now", "human|agent|escalation"),
    ("en", "Why why why did this happen to me I am a good person", "why|help|scam|recovery"),
    ("en", "I already called 1930 they didn't help what now useless system", "1930|useless|help|recovery"),
    ("en", "I am so angry they took everything I worked 20 years for this", "angry|savings|20|years|recovery"),
    ("en", "This is a scam your bot is also a scam", "scam|bot|help|frustrated"),
    ("en", "I want to talk to someone real not a bot right now", "human|agent|real|person|escalation"),
    ("en", "I am tired of these scammers calling me every single day", "tired|scammers|calling|help"),
    ("en", "Your useless bank did not stop the transaction fraud", "bank|not|stop|transaction|fraud"),
    ("en", "Nobody helps when you actually need what kind of system is this", "nobody|help|system|frustrated"),
]
for lang, msg, kw in angry_cases:
    uid = tc_id("TC_ANGRY")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"Angry: {msg[:50]}"])

# =====================================================================
# SECTION 50: VERY SHORT / TELEGRAPHIC INPUTS
# =====================================================================
short_cases = [
    ("en", "Scam", "scam|help"),
    ("en", "Hacked", "hacked|help|recovery"),
    ("en", "Fraud", "fraud|scam|help"),
    ("en", "Money gone", "money|gone|recovery"),
    ("en", "OTP shared", "otp|shared|help"),
    ("en", "Call from police", "police|call|scam"),
    ("en", "AnyDesk installed", "anydesk|installed|remote|scam"),
    ("en", "QR scanned", "qr|scanned|scam"),
    ("en", "Account empty", "account|empty|recovery"),
    ("en", "Blackmail", "blackmail|help|sextortion"),
    ("en", "Help needed", "help|needed|scam"),
    ("en", "Need recovery", "recovery|help"),
    ("en", "Link clicked", "link|clicked|phishing|help"),
    ("en", "SIM stopped", "sim|stopped|swap|help"),
    ("en", "Lost everything", "lost|everything|recovery|help"),
]
for lang, msg, kw in short_cases:
    uid = tc_id("TC_SHORT")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"Short: {msg}"])

# =====================================================================
# SECTION 51: NUMBERS / TRANSACTION ID INPUTS (Indian habit of quoting numbers)
# =====================================================================
number_cases = [
    ("en", "My UTR number is HDFC123456789 money not received", "utr|money|not|received|recovery"),
    ("en", "Transaction ID T2204150987654 se paise gaye", "transaction|id|paise|recovery"),
    ("en", "They took Rs 25,000 from my account reference 987654", "25000|account|recovery"),
    ("en", "Account number 12345678901 se paise nikal gaye", "account|number|paise|recovery"),
    ("en", "My IFSC HDFC0001234 mein fraud transaction hua", "ifsc|fraud|transaction|recovery"),
    ("en", "Order ID OD123456789 for Flipkart not delivered", "order|id|not|delivered|marketplace"),
    ("en", "Mobile number 9876543210 se OTP aa gaya maine bata diya", "otp|mobile|number|shared"),
    ("en", "Reference number 567890123 for the payment what to do", "reference|payment|recovery"),
    ("en", "My card number last 4 digits 4321 se unauthorized payment", "card|unauthorized|payment|block"),
    ("en", "Cust ID 12345678 se koi fraud kar raha hai", "customer|id|fraud|help"),
]
for lang, msg, kw in number_cases:
    uid = tc_id("TC_NUM")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"Numbers: {msg[:50]}"])

# =====================================================================
# SECTION 52: STORY / TIMELINE NARRATIVES
# =====================================================================
story_cases = [
    ("en", "First they called me then they sent a message then I clicked then money gone", "called|message|clicked|money|gone|recovery"),
    ("en", "It started yesterday when I got a WhatsApp message from an unknown number offering job", "whatsapp|job|offer|scam"),
    ("en", "Let me tell you from beginning I was on OLX selling my phone then buyer asked for my number", "olx|phone|buyer|scam"),
    ("en", "My problem is like this I needed money urgently so I searched online loan app then...", "loan|app|urgent|scam"),
    ("en", "There was this message that looked like it came from SBI and I clicked the link because it looked real", "sbi|message|link|phishing"),
    ("en", "So basically what happened is my friend added me to a Telegram group where they give trading tips", "telegram|trading|group|scam"),
    ("en", "I was just scrolling Instagram and saw this ad for work from home I thought why not try", "instagram|wfh|ad|scam"),
    ("en", "Maine socha koi problem nahi hai QR code scan kar liya lekin ulta paise kat gaye", "qr|scan|socha|ultra|paise|gaye"),
    ("en", "Ek din pehle ek call aaya unhone kaha aapka SIM block ho jayega maine dar ke OTP de diya", "call|sim|block|otp|diya"),
    ("en", "Pehle unhone kaha ki aapke naam par parcel hai phir bola custom clearance chahiye", "parcel|custom|clearance|scam"),
]
for lang, msg, kw in story_cases:
    uid = tc_id("TC_STORY")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"Story: {msg[:50]}"])

# =====================================================================
# SECTION 53: ELDERLY / VULNERABLE USER PATTERNS
# =====================================================================
elderly_cases = [
    ("en", "Beta mere account se paise nikal gaye kya karun", "beta|account|paise|help"),
    ("en", "Mera pension ka account hack ho gaya koi bachao", "pension|account|hack|help"),
    ("en", "I am 70 years old they took my pension money", "70|pension|money|gone|help"),
    ("en", "Beta ek call aaya bank se bola account block maine kuch diya", "call|bank|account|block"),
    ("en", "I don't understand technology someone called and I did what they said", "dont|understand|call|scam"),
    ("en", "Mera mobile kharab ho gaya hai I think virus aaya hai", "mobile|virus|help"),
    ("en", "Mere bete ka phone aaya tha paise chahiye emergency maine bhej diye", "beta|phone|emergency|money"),
    ("en", "I got a message and it said my life insurance policy will end", "insurance|policy|message|scam"),
    ("en", "Someone came to my door saying they are from bank and took my passbook", "door|bank|passbook|scam"),
    ("en", "Meri biwi ne kisi ko phone pe OTP bata diya ab kya hoga", "biwi|otp|phone|help"),
]
for lang, msg, kw in elderly_cases:
    uid = tc_id("TC_ELDERLY")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"Elderly: {msg[:50]}"])

# =====================================================================
# SECTION 54: COPY-PASTE / SCAM MESSAGE TEXT REPORTING
# =====================================================================
copypaste_cases = [
    ("en", "I got this message: Dear Customer your SBI bank account will be suspended update KYC immediately", "sbi|kyc|immediately|phishing"),
    ("en", "They sent: Congratulations you won 25 Lakhs in HDFC Lucky Draw contact agent for processing", "lucky|draw|25|lakh|processing"),
    ("en", "SMS says: Your Aadhaar card will be deactivated if not updated at aadhaar-gov.in NOW", "aadhaar|deactivated|update|phishing"),
    ("en", "Message: Your order from Amazon could not be delivered click to reschedule", "amazon|delivery|link|phishing"),
    ("en", "They wrote: I am a US army officer stationed in Syria I need your help to transfer money", "army|syria|money|transfer|scam"),
    ("en", "WhatsApp text: Earn daily 5000 by doing simple tasks on YouTube contact for registration", "earn|daily|tasks|registration|job"),
    ("en", "Message reads: Your FASTag is low balance auto-debit failed pay now avoid penalty", "fastag|balance|pay|link|scam"),
    ("en", "They sent: Free iPhone 15 just pay 99 shipping charges limited offer", "iphone|free|shipping|scam"),
    ("en", "SMS: Your ICICI credit card reward points are expiring redeem now at icici-offers.com", "credit|card|reward|redeem|phishing"),
    ("en", "I got this email: Netflix payment failed update billing details to continue membership", "netflix|billing|update|phishing"),
]
for lang, msg, kw in copypaste_cases:
    uid = tc_id("TC_COPY")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"Copy-paste: {msg[:50]}. . ."])

# =====================================================================
# SECTION 55: MORE MULTI-TURN FLOWS (complex journeys)
# =====================================================================
multi_cases = [
    ("en,multi-turn", "I received a call from a fake customer care number|They said my Amazon account has been hacked|They asked for OTP to secure it|I gave them the OTP|Now money is gone from my account", "customer|care|otp|money|gone|recovery", "phishing", "Flow2", "Multi-turn: Fake Amazon care -> OTP -> recovery"),
    ("en,multi-turn", "I clicked a link for free mobile recharge|Yes I entered my mobile number|Then they asked for OTP|I gave OTP|My phone stopped working", "link|recharge|otp|phone|stopped|sim", "sim_swap", "Flow2", "Multi-turn: Free recharge link -> OTP disclosure -> SIM swap"),
    ("en,multi-turn", "Someone on Telegram offered me part time job|I paid 500 registration fee|Now they want 2000 for training|I paid that too|Now they are asking more money", "telegram|job|registration|fee|paid|scam", "job_fraud", "", "Multi-turn: Telegram job scam progressive payments"),
    ("en,multi-turn", "My father got a video call from police|Police said he is involved in money laundering|They asked for 1 lakh for case settlement|He wants to transfer money|I told him not to", "police|video|call|laundering|scam", "digital_arrest", "Flow4", "Multi-turn: Digital arrest of parent -> preventive"),
    ("hing,multi-turn", "Maine OLX par phone bechne dala|Buyer ne QR bheja payment lene ke liye|Maine scan kiya|Paise nahi aaye ulta mere account se gaye|Ab kya karun", "olx|qr|scan|paise|gaye|scam", "marketplace_fraud", "Flow2", "Multi-turn: OLX -> QR scam -> recovery"),
    ("en,multi-turn", "I got a loan app installed|They asked for contacts and gallery access|I gave them access|Now they are threatening to send my photos to family|They want 50000 rupees", "loan|app|threat|photos|blackmail", "", "", "Multi-turn: Loan app -> data theft -> blackmail"),
    ("en,multi-turn", "I invested in a crypto site recommended by a friend|I put in 50000 initially|Then 100000 more when the profits showed|Now the site is not opening|Friend not responding either", "crypto|invest|friend|site|down|scam", "investment_scam", "", "Multi-turn: Friend referral -> crypto invest -> platform shut"),
    ("en,multi-turn", "I got a message from my daughter's WhatsApp saying she needs money|Then the person called and sounded like her|I transferred 25000|Now I realize it was a voice clone scam", "daughter|whatsapp|voice|clone|transfer", "", "Flow2", "Multi-turn: AI voice clone -> family emergency -> paid"),
]
for row in multi_cases:
    msg_part = ",".join(row[0].split(",")[1:]) if "," in row[0] else row[0]
    lang = row[0].split(",")[0] if "," in row[0] else row[0]
    kw = row[1]
    cls = row[2] if len(row) > 2 else ""
    journey = row[3] if len(row) > 3 else ""
    notes = row[4] if len(row) > 4 else ""
    uid = tc_id("TC_MTFLOW")
    cases.append([uid, lang, "multi-turn", msg_part, kw, cls, journey, notes])

# =====================================================================
# SECTION 56: MORE EDGE CASES (creative inputs)
# =====================================================================
edge_more_cases = [
    ("en", "😂😂😂😂😂", "scam|help", "Emoji-only laughter"),
    ("en", "???????", "scam|help", "Question marks only"),
    ("en", "...........", "scam|help", "Dots only"),
    ("en", "No", "no|scam|help", "Single word: no"),
    ("en", "Yes", "yes|scam|help", "Single word: yes"),
    ("en", "Maybe", "not|sure|check|help", "Single word: maybe"),
    ("en", "Ok", "help|scam", "Single word: ok"),
    ("en", "Thanks", "welcome|help", "Thanks feedback"),
    ("en", "I don't know", "dont|know|scam|help", "Uncertain user"),
    ("en", "My phone number is 9876543210", "phone|scam|help", "Number only"),
    ("en", "What is phishing", "phishing|explain|cyber", "Educational query"),
    ("en", "How to stay safe online", "safe|online|tips|preventive", "Safety education"),
    ("en", "Please call me back", "call|back|help|escalate", "Request callback"),
    ("en", "I want to report a cyber crime", "report|cyber|crime|1930", "Report request"),
    ("en", "Where is the nearest police station", "police|station|help|cyber", "Find police"),
]
for lang, msg, kw, notes in edge_more_cases:
    uid = tc_id("TC_EDGE2")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", notes or f"Edge: {msg[:40]}"])

# =====================================================================
# SECTION 57: LOCATION-SPECIFIC SCENARIOS
# =====================================================================
location_cases = [
    ("en", "I am in Mumbai someone came to my shop for credit card machine replacement scam", "mumbai|card|machine|replacement|scam"),
    ("en", "Bangalore mein PG owner deposit nahi lauta raha", "bangalore|pg|deposit|refund"),
    ("en", "Delhi mein OLX par phone lena tha dhoka ho gaya", "delhi|olx|phone|scam"),
    ("en", "Pune mein flat book kiya agent gayab", "pune|flat|agent|scam"),
    ("en", "Chennai la irundhu oru call vandhuchu bank nu soldranga", "chennai|bank|call|scam"),
    ("en", "Hyderabad mein real estate mein fraud hua", "hyderabad|real|estate|fraud"),
    ("en", "Kolkata mein job consultancy se registration fee liya job nahi diya", "kolkata|job|consultancy|fee"),
    ("en", "Ahmedabad mein fake gold jewellery becha", "ahmedabad|gold|fake|scam"),
    ("en", "Jaipur mein tourist package book kiya scam ho gaya", "jaipur|tourist|package|scam"),
    ("en", "Lucknow mein ATM machine replacement fraud dekha", "lucknow|atm|replacement|fraud"),
]
for lang, msg, kw in location_cases:
    uid = tc_id("TC_LOCATION")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"Location: {msg[:50]}"])

# =====================================================================
# SECTION 58: REGIONAL LANGUAGE WORDS MIXED
# =====================================================================
regional_cases = [
    ("en", "Yenna stalk market la invest pannen loss aagiduchu", "stock|market|invest|loss"),
    ("en", "Naa OTP share pannen ippo enna pannanum", "otp|share|help"),
    ("en", "Naaku evaro phone chesi OTP adigaru ichhanu", "phone|otp|share|help"),
    ("en", "Maja account hack zala kay karaych", "account|hack|help"),
    ("en", "Mera paisa ud gaya babu kuch karo", "paisa|gaya|help"),
    ("en", "Koroti UPI thettu account ku pochu help mame", "upi|wrong|account|help"),
    ("en", "Saar mere sath thoda bahut fraud ho gaya hai", "saar|fraud|help"),
    ("en", "Anna bank account la irundu pannam pochu help pannunga", "anna|bank|account|money|gone"),
    ("en", "Bhai ek call aaya tha bank se bhai maine OTP de diya", "bhai|call|otp|diya|scam"),
    ("en", "Dost mujhe kisi ne blackmail kiya hai help karo", "dost|blackmail|help"),
]
for lang, msg, kw in regional_cases:
    uid = tc_id("TC_REGIONAL")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"Regional: {msg[:50]}"])

# =====================================================================
# SECTION 59: URGENCY / TIME-SENSITIVE VARIANTS
# =====================================================================
urgency_cases = [
    ("en", "They are on the phone with me right now what do I tell them", "phone|right|now|urgent|help"),
    ("en", "I am at the ATM they are telling me what to do should I do it", "atm|calling|urgent|help"),
    ("en", "I already sent the money can I get it back please tell quickly", "already|sent|money|recovery|urgent"),
    ("en", "Transaction is processing right now can I stop it", "processing|stop|transaction|urgent"),
    ("en", "They are asking me to download an app should I do it", "download|app|asking|urgent|remote"),
    ("en", "I am about to pay 50000 to them please tell me yes or no", "about|pay|urgent|scam"),
    ("en", "They said my account will be closed in 2 hours what should I do", "account|closed|hours|urgent|scam"),
    ("en", "I have 10 minutes to transfer otherwise they will arrest me", "10|minutes|transfer|arrest|urgent"),
    ("en", "Immediate help needed my wife is crying they took everything", "immediate|wife|crying|help|scam"),
    ("en", "They said they will delete my data if I don't pay by tonight", "delete|data|pay|tonight|urgent"),
]
for lang, msg, kw in urgency_cases:
    uid = tc_id("TC_URGENT")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"Urgent: {msg[:50]}"])

# =====================================================================
# SECTION 60: REPETITIVE / LOOPING USER
# =====================================================================
repeat_cases = [
    ("en", "Hello", "hello|help|scam"),
    ("en", "Hello are you there", "hello|help|scam"),
    ("en", "Are you a real person", "real|person|bot|help"),
    ("en", "Are you there can you help me", "help|scam"),
    ("en", "Are you still there", "help|still|there"),
    ("en", "Why are you not answering", "help|scam|answer"),
    ("en", "I am waiting for your reply please reply", "reply|waiting|help"),
    ("en", "My problem is very serious please listen", "serious|problem|help|scam"),
    ("en", "Please please please listen to me", "please|listen|help"),
    ("en", "I don't think you understand my problem", "understand|problem|help"),
]
for lang, msg, kw in repeat_cases:
    uid = tc_id("TC_LOOP")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"Loop: {msg}"])

# =====================================================================
# SECTION 61: SPECIFIC SCAM NARRATIVES - NEW SCENARIOS
# =====================================================================
special_cases = [
    ("en", "I got an email saying my website domain is expiring renew immediately", "domain|renew|urgent|scam"),
    ("en", "My Instagram account was hacked someone posted scam links on my story", "instagram|hacked|scam|links"),
    ("en", "We received a ransom note saying our company data will be leaked", "ransom|data|leak|company"),
    ("en", "I paid for visa application through an agent now I think it's fake", "visa|application|agent|fake"),
    ("en", "Someone is using my photos to create fake profiles on dating sites", "fake|profile|photos|identity"),
    ("en", "My credit score dropped suddenly someone took loan in my name", "credit|score|loan|identity"),
    ("en", "They threatened to send morons to my house what to do for safety", "threat|house|safety|scam"),
    ("en", "I won a free trip to Dubai just pay visa processing fee scam hai", "trip|dubai|visa|fee|scam"),
    ("en", "Fake advocate called saying your son is in jail send money for bail", "advocate|son|jail|bail|scam"),
    ("en", "I received a legal notice by email saying I have to pay fine immediately", "legal|notice|fine|pay|scam"),
]
for lang, msg, kw in special_cases:
    uid = tc_id("TC_SPECIAL")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"Special: {msg[:50]}"])

# =====================================================================
# SECTION 62: MORE NEGATIVE / GENUINE CASES
# =====================================================================
negative_more_cases = [
    ("en", "I want to transfer money to my sister is it safe to use UPI", "upi|safe|transfer"),
    ("en", "How do I create a strong password", "password|strong|secure"),
    ("en", "What is two factor authentication", "two|factor|authentication|security"),
    ("en", "Should I use the same password for all websites", "password|different|security"),
    ("en", "Is it safe to save card details on Amazon", "card|details|amazon|safe"),
    ("en", "How to check if my Aadhaar is linked to my mobile number", "aadhaar|mobile|linked|check"),
    ("en", "My genuine Flipkart order is delayed should I worry", "flipkart|order|delayed|genuine"),
    ("en", "Is Paytm safe to use for daily transactions", "paytm|safe|transactions"),
    ("en", "My bank sent me an SMS with transaction alert is this normal", "bank|sms|transaction|normal"),
    ("en", "I received a gift from my friend should I pay customs", "gift|customs|friend|genuine"),
]
for lang, msg, kw in negative_more_cases:
    uid = tc_id("TC_NEG2")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"Negative: {msg[:50]}"])

# =====================================================================
# SECTION 63: WhatsApp / SMS FORWARD MESSAGES (how Indians forward chains)
# =====================================================================
forward_cases = [
    ("en", "Forwarded: This is serious WhatsApp is going to charge from tomorrow forward this to 10 people", "forward|whatsapp|charge|scam"),
    ("en", "Forwarded: Coca Cola giving free fridge click here to claim", "coca|cola|free|fridge|scam"),
    ("en", "Forwarded: Jio is giving free 5G SIM upgrade click link", "jio|free|5g|upgrade|scam"),
    ("en", "Forwarded: Your phone will be deactivated in 24 hours register now", "phone|deactivated|register|scam"),
    ("en", "Forwarded: This message is from WhatsApp CEO Mark Zuckerberg we are giving free data", "zuckerberg|free|data|scam"),
    ("en", "Forwarded: LIC policy holders special bonus update your KYC", "lic|bonus|kyc|scam"),
    ("en", "Forwarded: Red Cross giving 50000 to everyone click here", "red|cross|50000|scam"),
    ("en", "Forwarded: SBI customer special offer limited period update now", "sbi|customer|offer|update|scam"),
    ("en", "Forwarded: PM Modi government scheme 5000 monthly to all citizens register", "modi|scheme|5000|register|scam"),
    ("en", "Forwarded: WhatsApp gold version available only for selected users", "whatsapp|gold|version|scam"),
]
for lang, msg, kw in forward_cases:
    uid = tc_id("TC_FWD")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"Forwarded: {msg[:50]}"])

# =====================================================================
# SECTION 64: MORE OUT OF SCOPE (expanding the non-cyber queries)
# =====================================================================
oos_more_cases = [
    ("en", "What is the capital of France", "cyber|fraud|assistance"),
    ("en", "How to make biryani recipe tell me", "cyber|fraud|help"),
    ("en", "Who won the cricket match yesterday", "cyber|fraud|assistance"),
    ("en", "Can you book a cab for me", "cyber|fraud|assistance"),
    ("en", "What is the meaning of life", "cyber|fraud|assistance"),
    ("en", "Can you write a poem about friendship", "cyber|fraud|assistance"),
    ("en", "Tell me a joke please", "cyber|fraud|assistance"),
    ("en", "What is 2+2", "cyber|fraud|assistance"),
    ("en", "How tall is Mount Everest", "cyber|fraud|assistance"),
    ("en", "Who is the Prime Minister of India", "cyber|fraud|assistance"),
    ("en", "Can you help me with my homework", "cyber|fraud|assistance"),
    ("en", "What time is it right now", "cyber|fraud|assistance"),
]
for lang, msg, kw in oos_more_cases:
    uid = tc_id("TC_OOS2")
    cases.append([uid, lang, "single-turn", msg, kw, "", "", f"OOS: {msg}"])

# ── Write CSV ────────────────────────────────────────────────────────
output_path = os.path.join(os.path.dirname(__file__), "comprehensive_test_cases_extended.csv")
with open(output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(HEADER)

    # Write section comments and data
    current_section = ""
    for row in cases:
        writer.writerow(row)

total = len(cases)
print(f"Generated {total} new test cases → {output_path}")
print(f"Added to existing 171 → total ~{total + 171} test cases")
