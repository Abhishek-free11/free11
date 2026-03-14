import json, copy

def load(lang):
    with open(f'/app/frontend/src/locales/{lang}.json') as f:
        return json.load(f)

def save(lang, data):
    with open(f'/app/frontend/src/locales/{lang}.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ─── Missing sections per language ───────────────────────────────────────────

MISSING = {
    "hi": {
        "cardgames_page": {
            "select_game": "खेल चुनें", "available_rooms": "उपलब्ध कमरे", "active_games": "आपके सक्रिय खेल",
            "join_code": "निजी कमरे में शामिल हों", "enter_code": "कमरे का कोड दर्ज करें", "join": "शामिल हों",
            "no_rooms": "कोई कमरा उपलब्ध नहीं", "create_room": "कमरा बनाएं", "join_by_code": "कोड से शामिल हों",
            "loading": "लोड हो रहा है...", "copy_code": "कॉपी करें", "invite_friend": "मित्र को आमंत्रित करें",
            "how_it_works": "यह कैसे काम करता है", "step1": "एक खेल चुनें", "step2": "कमरे में शामिल हों या बनाएं",
            "step3": "खेलें और कमाएं"
        },
        "support_page": {
            "title": "सहायता और समर्थन", "chat_tab": "चैट", "tickets_tab": "टिकट",
            "type_message": "संदेश टाइप करें...", "send": "भेजें", "create_ticket": "टिकट बनाएं",
            "no_tickets": "अभी तक कोई टिकट नहीं", "loading": "लोड हो रहा है..."
        },
        "notifications": {
            "title": "सूचनाएं", "enable": "सूचनाएं सक्षम करें", "settings": "सूचना सेटिंग्स"
        }
    },
    "ta": {
        "landing": {
            "headline1": "சரியான முடிவுகள் எடுங்கள்.", "headline2": "உண்மையான வெகுமதிகள் பெறுங்கள்.",
            "subheadline": "FREE11 - விளையாட்டு அறிவை உண்மையான பொருட்களாக மாற்றும் தளம்.",
            "hero_desc": "கணிப்பு செய்யுங்கள், விளையாடுங்கள், பணிகள் முடியுங்கள், லீடர்போர்டில் ஏறுங்கள்.",
            "start_playing": "விளையாட தொடங்கு", "explore_games": "விளையாட்டுகளை ஆராயுங்கள்",
            "start": "தொடங்கு", "login": "உள்நுழை", "sign_in": "உள்நுழை",
            "platform_title": "FREE11 இல் எல்லாமே", "platform_subtitle": "ஒரு தளம். ஆறு வழிகளில் சம்பாதி.",
            "feature1_title": "நேரடி போட்டி கணிப்பு", "feature1_desc": "நேரடியாக போட்டி தருணங்களை கணியுங்கள்.",
            "feature2_title": "திறன் அடிப்படையிலான விளையாட்டுகள்", "feature2_desc": "ரம்மி, போக்கர், டீன் பட்டி விளையாடுங்கள்.",
            "feature3_title": "பணிகள் & தினசரி சவால்கள்", "feature3_desc": "பணிகள், ஸ்ட்ரீக்குகள் மூலம் நாணயங்கள் சம்பாதியுங்கள்.",
            "feature4_title": "லீடர்போர்டுகள்", "feature4_desc": "நண்பர்களுடன் போட்டியிட்டு உயருங்கள்.",
            "feature5_title": "வெகுமதி கடை", "feature5_desc": "நாணயங்களை வவுச்சர்களுக்கு மாற்றுங்கள்.",
            "feature6_title": "FREE Bucks", "feature6_desc": "பிரீமியம் போட்டிகளில் கலந்துகொள்ளுங்கள்.",
            "how_it_works": "எப்படி வேலை செய்கிறது",
            "step1_title": "கணக்கு உருவாக்கு", "step1_desc": "60 வினாடிகளில் இலவசமாக பதிவு செய்யுங்கள்",
            "step2_title": "விளையாடு & கணி", "step2_desc": "போட்டிகளை கணியுங்கள், விளையாடுங்கள்",
            "step3_title": "நாணயங்கள் சம்பாதி", "step3_desc": "ஒவ்வொரு சரியான கணிப்பும் நாணயங்கள் தரும்",
            "step4_title": "பொருட்கள் பெறு", "step4_desc": "நாணயங்களை வெகுமதிகளுக்கு மாற்றுங்கள்",
            "cta_headline": "இன்றே FREE11 பயணத்தை தொடங்குங்கள்.",
            "cta_desc": "ஆயிரக்கணக்கான விளையாட்டு ரசிகர்களுடன் சேருங்கள்.",
            "create_account": "கணக்கு உருவாக்கு", "login_btn": "உள்நுழை",
            "disclaimer_title": "மறுப்பு:", "disclaimer_text": "FREE11 ஒரு திறன் அடிப்படையிலான தளம். இது சூதாட்டம் அல்ல. 18+ மட்டும்.",
            "tagline_coins": "திறன் → நாணயங்கள் → உண்மையான பொருட்கள்",
            "copyright_suffix": "உங்கள் அறிவு, உண்மையான வெகுமதிகள்"
        },
        "leaderboard_page": {
            "title": "லீடர்போர்டுகள்", "subtitle": "திறன் அடிப்படையில் போட்டியிடுங்கள்!",
            "loading": "லீடர்போர்டுகள் ஏற்றுகிறது...", "global_tab": "உலகளாவிய",
            "weekly_tab": "வாராந்திர", "streak_tab": "ஸ்ட்ரீக்குகள்",
            "global_title": "உலக தரவரிசைகள்", "global_desc": "அனைத்து நேர கணிப்பு துல்லியம்",
            "weekly_title": "வாராந்திர தரவரிசைகள்", "weekly_desc": "இந்த வாரத்தின் சிறந்த கணிப்பாளர்கள்",
            "streak_title": "ஸ்ட்ரீக் ராஜாக்கள்", "streak_desc": "தொடர் சரியான கணிப்புகள்",
            "no_global": "இன்னும் தரவரிசைகள் இல்லை. கணிக்க தொடங்குங்கள்!",
            "no_weekly": "இந்த வாரம் கணிப்புகள் இல்லை.", "no_streak": "ஸ்ட்ரீக்குகள் இல்லை.",
            "duels_title": "கணிப்பு மோதல்கள்", "duels_desc": "நண்பர்களை சவால் செய்யுங்கள்!",
            "activity_title": "செயல்பாடு ஊட்டம்",
            "incoming_challenges": "வரும் சவால்கள்", "active_duels": "செயலில் மோதல்கள்",
            "no_duels": "மோதல்கள் இல்லை. யாரையாவது சவால் செய்யுங்கள்!",
            "no_activity": "சமீபத்திய செயல்பாடு இல்லை", "challenged_you": "உங்களை சவால் செய்தார்!",
            "accept": "ஏற்கவும்", "decline": "மறுக்கவும்", "challenge_btn": "மோதலுக்கு சவால் செய்",
            "won": "வெற்றி", "played": "விளையாடியது", "win_rate": "வெற்றி விகிதம்",
            "you": "நீங்கள்:", "them": "அவர்கள்:", "accuracy_pct": "துல்லியம்", "correct_label": "சரி"
        },
        "referrals_page": {
            "title": "பரிந்துரை & சம்பாதி", "your_code": "உங்கள் பரிந்துரை குறியீடு",
            "share_msg": "இந்த குறியீட்டை நண்பர்களுடன் பகிருங்கள். இருவரும் நாணயங்கள் சம்பாதிப்பீர்கள்!",
            "referrals_label": "பரிந்துரைகள்", "earned_label": "சம்பாதித்தது", "per_invite_label": "ஒரு அழைப்புக்கு",
            "have_code": "பரிந்துரை குறியீடு இருக்கிறதா?", "enter_code": "குறியீடு உள்ளிடவும்",
            "apply": "பயன்படுத்து", "how_it_works": "எப்படி வேலை செய்கிறது",
            "step1": "உங்கள் தனிப்பட்ட குறியீட்டை பகிருங்கள்",
            "step2": "நண்பர் பதிவு செய்து குறியீடு உள்ளிடுகிறார்",
            "step3_prefix": "நீங்கள் பெறுவீர்கள்", "step3_suffix": "நாணயங்கள், நண்பருக்கு 25 நாணயங்கள்"
        },
        "cardgames_page": {
            "select_game": "விளையாட்டு தேர்வு", "available_rooms": "கிடைக்கும் அறைகள்",
            "active_games": "உங்கள் செயலில் விளையாட்டுகள்", "join_code": "தனிப்பட்ட அறை சேரு",
            "enter_code": "அறை குறியீடு உள்ளிடவும்", "join": "சேர", "no_rooms": "அறைகள் இல்லை",
            "create_room": "அறை உருவாக்கு", "join_by_code": "குறியீட்டால் சேரு",
            "loading": "ஏற்றுகிறது...", "copy_code": "நகல்", "invite_friend": "நண்பரை அழை",
            "how_it_works": "எப்படி வேலை செய்கிறது",
            "step1": "ஒரு விளையாட்டு தேர்வு", "step2": "அறையில் சேரு அல்லது உருவாக்கு", "step3": "விளையாடி சம்பாதி"
        },
        "support_page": {
            "title": "உதவி & ஆதரவு", "chat_tab": "அரட்டை", "tickets_tab": "டிக்கெட்",
            "type_message": "செய்தி தட்டச்சு செய்யவும்...", "send": "அனுப்பு",
            "create_ticket": "டிக்கெட் உருவாக்கு", "no_tickets": "டிக்கெட்கள் இல்லை",
            "loading": "ஏற்றுகிறது..."
        },
        "notifications": {
            "title": "அறிவிப்புகள்", "enable": "அறிவிப்புகளை இயக்கு", "settings": "அறிவிப்பு அமைப்புகள்"
        }
    }
}

# Bengali (bn)
MISSING["bn"] = {
    "landing": {
        "headline1": "সঠিক সিদ্ধান্ত নিন।", "headline2": "বাস্তব পুরস্কার পান।",
        "subheadline": "FREE11 - আপনার ক্রীড়া জ্ঞান বাস্তব পণ্যে রূপান্তরিত করুন।",
        "hero_desc": "ম্যাচ মুহূর্ত ভবিষ্যদ্বাণী করুন, গেম খেলুন, মিশন সম্পন্ন করুন।",
        "start_playing": "খেলা শুরু করুন", "explore_games": "গেম অন্বেষণ করুন",
        "start": "শুরু করুন", "login": "লগইন", "sign_in": "সাইন ইন",
        "platform_title": "FREE11-এ সব কিছু", "platform_subtitle": "একটি প্ল্যাটফর্ম। ছয়টি উপায়ে আয় করুন।",
        "feature1_title": "লাইভ ম্যাচ ভবিষ্যদ্বাণী", "feature1_desc": "রিয়েল টাইমে ম্যাচ মুহূর্ত ভবিষ্যদ্বাণী করুন।",
        "feature2_title": "দক্ষতা-ভিত্তিক গেম", "feature2_desc": "রামি, পোকার এবং তিন পাত্তি খেলুন।",
        "feature3_title": "মিশন ও দৈনিক চ্যালেঞ্জ", "feature3_desc": "কাজ, স্ট্রিক এবং স্পিন সম্পন্ন করে কয়েন উপার্জন করুন।",
        "feature4_title": "লিডারবোর্ড", "feature4_desc": "বন্ধুদের সাথে প্রতিযোগিতা করুন।",
        "feature5_title": "পুরস্কার স্টোর", "feature5_desc": "কয়েন দিয়ে ভাউচার এবং পণ্য রিডিম করুন।",
        "feature6_title": "FREE Bucks", "feature6_desc": "প্রিমিয়াম প্রতিযোগিতায় অ্যাক্সেস করুন।",
        "how_it_works": "এটি কীভাবে কাজ করে",
        "step1_title": "অ্যাকাউন্ট তৈরি করুন", "step1_desc": "৬০ সেকেন্ডের মধ্যে বিনামূল্যে সাইন আপ করুন",
        "step2_title": "খেলুন এবং ভবিষ্যদ্বাণী করুন", "step2_desc": "ম্যাচ ভবিষ্যদ্বাণী করুন, গেম খেলুন",
        "step3_title": "কয়েন উপার্জন করুন", "step3_desc": "প্রতিটি সঠিক কল কয়েন উপার্জন করে",
        "step4_title": "পণ্য পান", "step4_desc": "কয়েন দিয়ে বাস্তব পণ্য রিডিম করুন",
        "cta_headline": "আজই আপনার FREE11 যাত্রা শুরু করুন।",
        "cta_desc": "হাজার হাজার ক্রীড়া ভক্তদের সাথে যোগ দিন।",
        "create_account": "অ্যাকাউন্ট তৈরি করুন", "login_btn": "লগইন",
        "disclaimer_title": "দাবিত্যাগ:", "disclaimer_text": "FREE11 একটি দক্ষতা-ভিত্তিক প্ল্যাটফর্ম। এটি জুয়া নয়। ১৮+ শুধুমাত্র।",
        "tagline_coins": "দক্ষতা → কয়েন → বাস্তব পণ্য",
        "copyright_suffix": "আপনার জ্ঞান, বাস্তব পুরস্কার"
    },
    "leaderboard_page": {
        "title": "লিডারবোর্ড", "subtitle": "দক্ষতায় প্রতিযোগিতা করুন!",
        "loading": "লিডারবোর্ড লোড হচ্ছে...", "global_tab": "বৈশ্বিক",
        "weekly_tab": "সাপ্তাহিক", "streak_tab": "স্ট্রিক",
        "global_title": "বৈশ্বিক র‍্যাংকিং", "global_desc": "সর্বকালের ভবিষ্যদ্বাণী নির্ভুলতা",
        "weekly_title": "সাপ্তাহিক র‍্যাংকিং", "weekly_desc": "এই সপ্তাহের শীর্ষ ভবিষ্যদ্বাণীকারীরা",
        "streak_title": "স্ট্রিক কিংস", "streak_desc": "সর্বদীর্ঘ ধারাবাহিক সঠিক ভবিষ্যদ্বাণী",
        "no_global": "এখনও র‍্যাংকিং নেই। ভবিষ্যদ্বাণী করতে শুরু করুন!",
        "no_weekly": "এই সপ্তাহে কোনো ভবিষ্যদ্বাণী নেই।", "no_streak": "কোনো স্ট্রিক নেই।",
        "duels_title": "প্রেডিকশন ডুয়েল", "duels_desc": "বন্ধুদের চ্যালেঞ্জ করুন!",
        "activity_title": "অ্যাক্টিভিটি ফিড",
        "incoming_challenges": "আসন্ন চ্যালেঞ্জ", "active_duels": "সক্রিয় ডুয়েল",
        "no_duels": "কোনো ডুয়েল নেই।", "no_activity": "কোনো সাম্প্রতিক কার্যক্রম নেই",
        "challenged_you": "আপনাকে চ্যালেঞ্জ করেছে!",
        "accept": "গ্রহণ করুন", "decline": "প্রত্যাখ্যান করুন", "challenge_btn": "ডুয়েলে চ্যালেঞ্জ করুন",
        "won": "জয়", "played": "খেলেছে", "win_rate": "জয়ের হার",
        "you": "আপনি:", "them": "তারা:", "accuracy_pct": "নির্ভুলতা", "correct_label": "সঠিক"
    },
    "referrals_page": {
        "title": "রেফার করুন এবং উপার্জন করুন", "your_code": "আপনার রেফারেল কোড",
        "share_msg": "এই কোডটি বন্ধুদের সাথে শেয়ার করুন। আপনি উভয়ই কয়েন উপার্জন করবেন!",
        "referrals_label": "রেফারেল", "earned_label": "উপার্জিত", "per_invite_label": "প্রতি আমন্ত্রণে",
        "have_code": "রেফারেল কোড আছে?", "enter_code": "কোড লিখুন",
        "apply": "প্রয়োগ করুন", "how_it_works": "এটি কীভাবে কাজ করে",
        "step1": "আপনার অনন্য কোড বন্ধুদের সাথে শেয়ার করুন",
        "step2": "বন্ধু সাইন আপ করে আপনার কোড লিখে",
        "step3_prefix": "আপনি পান", "step3_suffix": "কয়েন, বন্ধু পায় ২৫ কয়েন"
    },
    "cardgames_page": {
        "select_game": "গেম নির্বাচন করুন", "available_rooms": "উপলব্ধ রুম",
        "active_games": "আপনার সক্রিয় গেম", "join_code": "প্রাইভেট রুমে যোগ দিন",
        "enter_code": "রুম কোড লিখুন", "join": "যোগ দিন", "no_rooms": "কোনো রুম উপলব্ধ নেই",
        "create_room": "রুম তৈরি করুন", "join_by_code": "কোড দিয়ে যোগ দিন",
        "loading": "লোড হচ্ছে...", "copy_code": "কপি", "invite_friend": "বন্ধুকে আমন্ত্রণ করুন",
        "how_it_works": "এটি কীভাবে কাজ করে",
        "step1": "একটি গেম নির্বাচন করুন", "step2": "রুমে যোগ দিন বা তৈরি করুন", "step3": "খেলুন এবং উপার্জন করুন"
    },
    "support_page": {
        "title": "সহায়তা", "chat_tab": "চ্যাট", "tickets_tab": "টিকিট",
        "type_message": "বার্তা লিখুন...", "send": "পাঠান",
        "create_ticket": "টিকিট তৈরি করুন", "no_tickets": "কোনো টিকিট নেই",
        "loading": "লোড হচ্ছে..."
    },
    "notifications": {
        "title": "বিজ্ঞপ্তি", "enable": "বিজ্ঞপ্তি সক্ষম করুন", "settings": "বিজ্ঞপ্তি সেটিংস"
    }
}

# Telugu (te)
MISSING["te"] = {
    "landing": {
        "headline1": "సరైన నిర్ణయాలు తీసుకోండి.", "headline2": "నిజమైన బహుమతులు పొందండి.",
        "subheadline": "FREE11 - మీ క్రీడా జ్ఞానాన్ని నిజమైన ఉత్పత్తులుగా మార్చే వేదిక.",
        "hero_desc": "మ్యాచ్ క్షణాలను అంచనా వేయండి, ఆడండి, మిషన్లు పూర్తి చేయండి.",
        "start_playing": "ఆడటం ప్రారంభించండి", "explore_games": "ఆటలు అన్వేషించండి",
        "start": "ప్రారంభించండి", "login": "లాగిన్", "sign_in": "సైన్ ఇన్",
        "platform_title": "FREE11లో అన్నీ", "platform_subtitle": "ఒక వేదిక. ఆరు మార్గాల్లో సంపాదించండి.",
        "feature1_title": "లైవ్ మ్యాచ్ అంచనాలు", "feature1_desc": "నిజ సమయంలో మ్యాచ్ క్షణాలు అంచనా వేయండి.",
        "feature2_title": "నైపుణ్య ఆధారిత ఆటలు", "feature2_desc": "రమ్మీ, పోకర్, తీన్ పత్తీ ఆడండి.",
        "feature3_title": "మిషన్లు & రోజువారీ సవాళ్లు", "feature3_desc": "పనులు, స్ట్రీక్‌లు పూర్తి చేసి నాణేలు సంపాదించండి.",
        "feature4_title": "లీడర్‌బోర్డులు", "feature4_desc": "స్నేహితులతో పోటీ పడి ర్యాంకింగ్ పెంచుకోండి.",
        "feature5_title": "రివార్డ్ స్టోర్", "feature5_desc": "నాణేలతో వోచర్లు మరియు ఉత్పత్తులు రిడీమ్ చేయండి.",
        "feature6_title": "FREE Bucks", "feature6_desc": "ప్రీమియమ్ పోటీలు అన్‌లాక్ చేయండి.",
        "how_it_works": "ఇది ఎలా పని చేస్తుంది",
        "step1_title": "ఖాతా తయారుచేయండి", "step1_desc": "60 సెకన్లలో ఉచితంగా నమోదు చేయండి",
        "step2_title": "ఆడండి & అంచనా వేయండి", "step2_desc": "మ్యాచ్‌లు అంచనా వేయండి, ఆటలు ఆడండి",
        "step3_title": "నాణేలు సంపాదించండి", "step3_desc": "ప్రతి సరైన అంచనా నాణేలు ఇస్తుంది",
        "step4_title": "ఉత్పత్తులు పొందండి", "step4_desc": "నాణేలతో నిజమైన ఉత్పత్తులు రిడీమ్ చేయండి",
        "cta_headline": "ఈరోజే మీ FREE11 ప్రయాణం ప్రారంభించండి.",
        "cta_desc": "వేలాది క్రీడా అభిమానులతో చేరండి.",
        "create_account": "ఖాతా తయారుచేయండి", "login_btn": "లాగిన్",
        "disclaimer_title": "నిరాకరణ:", "disclaimer_text": "FREE11 నైపుణ్య ఆధారిత వేదిక. జూదం కాదు. 18+ మాత్రమే.",
        "tagline_coins": "నైపుణ్యం → నాణేలు → నిజమైన ఉత్పత్తులు",
        "copyright_suffix": "మీ జ్ఞానం, నిజమైన బహుమతులు"
    },
    "leaderboard_page": {
        "title": "లీడర్‌బోర్డులు", "subtitle": "నైపుణ్యంలో పోటీ పడండి!",
        "loading": "లీడర్‌బోర్డులు లోడ్ అవుతున్నాయి...", "global_tab": "ప్రపంచ",
        "weekly_tab": "వారాంత", "streak_tab": "స్ట్రీక్‌లు",
        "global_title": "ప్రపంచ ర్యాంకింగులు", "global_desc": "అన్నీ సమయ అంచనా ఖచ్చితత్వం",
        "weekly_title": "వారాంత ర్యాంకింగులు", "weekly_desc": "ఈ వారం అగ్ర అంచనాదారులు",
        "streak_title": "స్ట్రీక్ కింగ్స్", "streak_desc": "వరుస సరైన అంచనాలు",
        "no_global": "ఇంకా ర్యాంకింగులు లేవు. అంచనా వేయడం ప్రారంభించండి!",
        "no_weekly": "ఈ వారం అంచనాలు లేవు.", "no_streak": "స్ట్రీక్‌లు లేవు.",
        "duels_title": "ప్రెడిక్షన్ డ్యూయెల్స్", "duels_desc": "స్నేహితులను సవాలు చేయండి!",
        "activity_title": "యాక్టివిటీ ఫీడ్",
        "incoming_challenges": "వస్తున్న సవాళ్లు", "active_duels": "క్రియాశీల డ్యూయెల్స్",
        "no_duels": "డ్యూయెల్స్ లేవు.", "no_activity": "ఇటీవలి కార్యకలాపాలు లేవు",
        "challenged_you": "మిమ్మల్ని సవాలు చేశారు!",
        "accept": "అంగీకరించు", "decline": "తిరస్కరించు", "challenge_btn": "డ్యూయెల్‌కు సవాలు చేయండి",
        "won": "గెలిచింది", "played": "ఆడింది", "win_rate": "గెలుపు రేటు",
        "you": "మీరు:", "them": "వారు:", "accuracy_pct": "ఖచ్చితత్వం", "correct_label": "సరైనది"
    },
    "referrals_page": {
        "title": "రెఫర్ చేయండి & సంపాదించండి", "your_code": "మీ రెఫరల్ కోడ్",
        "share_msg": "ఈ కోడ్‌ను స్నేహితులతో పంచుకోండి. ఇద్దరూ నాణేలు సంపాదిస్తారు!",
        "referrals_label": "రెఫరల్స్", "earned_label": "సంపాదించారు", "per_invite_label": "ఆహ్వానానికి",
        "have_code": "రెఫరల్ కోడ్ ఉందా?", "enter_code": "కోడ్ నమోదు చేయండి",
        "apply": "వర్తింపచేయండి", "how_it_works": "ఇది ఎలా పని చేస్తుంది",
        "step1": "మీ ప్రత్యేక కోడ్ స్నేహితులతో పంచుకోండి",
        "step2": "స్నేహితుడు నమోదు చేసి మీ కోడ్ నమోదు చేస్తాడు",
        "step3_prefix": "మీరు పొందుతారు", "step3_suffix": "నాణేలు, స్నేహితుడు 25 నాణేలు పొందుతాడు"
    },
    "cardgames_page": {
        "select_game": "ఆట ఎంచుకోండి", "available_rooms": "అందుబాటులో ఉన్న గదులు",
        "active_games": "మీ క్రియాశీల ఆటలు", "join_code": "ప్రైవేట్ గదిలో చేరండి",
        "enter_code": "గది కోడ్ నమోదు చేయండి", "join": "చేరండి", "no_rooms": "గదులు అందుబాటులో లేవు",
        "create_room": "గది తయారుచేయండి", "join_by_code": "కోడ్‌తో చేరండి",
        "loading": "లోడ్ అవుతోంది...", "copy_code": "కాపీ", "invite_friend": "స్నేహితుడిని ఆహ్వానించండి",
        "how_it_works": "ఇది ఎలా పని చేస్తుంది",
        "step1": "ఒక ఆట ఎంచుకోండి", "step2": "గదిలో చేరండి లేదా తయారుచేయండి", "step3": "ఆడండి & సంపాదించండి"
    },
    "support_page": {
        "title": "సహాయం & మద్దతు", "chat_tab": "చాట్", "tickets_tab": "టికెట్లు",
        "type_message": "సందేశం టైప్ చేయండి...", "send": "పంపండి",
        "create_ticket": "టికెట్ తయారుచేయండి", "no_tickets": "టికెట్లు లేవు",
        "loading": "లోడ్ అవుతోంది..."
    },
    "notifications": {
        "title": "నోటిఫికేషన్లు", "enable": "నోటిఫికేషన్లు ప్రారంభించండి", "settings": "నోటిఫికేషన్ సెట్టింగులు"
    }
}

# ── Kannada (kn) — heavy missing ─────────────────────────────────────────────
MISSING["kn"] = {
    "earn_page": {
        "title": "ಕಾಯಿನ್ ಬೂಸ್ಟರ್‌ಗಳು", "subtitle": "ಬೋನಸ್ ಚಟುವಟಿಕೆಗಳೊಂದಿಗೆ ನಿಮ್ಮ ಆದಾಯವನ್ನು ವೇಗಗೊಳಿಸಿ",
        "supplementary": "ಇವು ಕ್ರಿಕೆಟ್ ಊಹೆಗಳಿಗೆ ಪೂರಕ", "how_to_earn": "ಹೇಗೆ ಗಳಿಸುವುದು",
        "mini_games_tab": "ಮಿನಿ ಆಟಗಳು", "tasks_tab": "ಕಾರ್ಯಗಳು",
        "fantasy_contests": "ಫ್ಯಾಂಟಸಿ ಸ್ಪರ್ಧೆಗಳು", "fantasy_desc": "ಕನಸಿನ ತಂಡ ಮಾಡಿ ಸ್ಪರ್ಧಿಸಿ.",
        "up_to_500": "ಪ್ರತಿ ಸ್ಪರ್ಧೆಗೆ 500 ಕಾಯಿನ್‌ಗಳ ವರೆಗೆ",
        "match_winner": "ಮ್ಯಾಚ್ ವಿನ್ನರ್ ಊಹೆ", "match_winner_desc": "ಗೆಲ್ಲುವ ತಂಡವನ್ನು ಊಹಿಸಿ.",
        "fifty_per": "ಸರಿಯಾದ ಊಹೆಗೆ 50 ಕಾಯಿನ್‌ಗಳು",
        "over_outcome": "ಓವರ್ ಫಲಿತಾಂಶ ಊಹೆ", "over_desc": "ಲೈವ್ ಮ್ಯಾಚ್‌ಗಳಲ್ಲಿ ರನ್‌ಗಳನ್ನು ಊಹಿಸಿ.",
        "twenty_five": "ಸರಿಯಾದ ಊಹೆಗೆ 25 ಕಾಯಿನ್‌ಗಳು",
        "ball_by_ball": "ಚೆಂಡು-ಚೆಂಡಾಗಿ", "ball_desc": "ಡೆಲಿವರಿ ಫಲಿತಾಂಶಗಳನ್ನು ಊಹಿಸಿ.",
        "five_fifteen": "ಸರಿಯಾದ ಊಹೆಗೆ 5-15 ಕಾಯಿನ್‌ಗಳು",
        "mini_tasks": "ಮಿನಿ ಆಟಗಳು ಮತ್ತು ಕಾರ್ಯಗಳು", "mini_desc": "ದೈನಂದಿನ ಆಟಗಳನ್ನು ಆಡಿ.",
        "ten_hundred": "ಚಟುವಟಿಕೆಗೆ 10-100 ಕಾಯಿನ್‌ಗಳು",
        "quiz_title": "ಕ್ರಿಕೆಟ್ ಕ್ವಿಜ್ ಸವಾಲು", "quiz_desc": "ನಿಮ್ಮ ಕ್ರಿಕೆಟ್ ಜ್ಞಾನವನ್ನು ಪರೀಕ್ಷಿಸಿ",
        "up_to_50": "50 ಕಾಯಿನ್‌ಗಳ ವರೆಗೆ", "play_now": "ಈಗ ಆಡು",
        "lucky_spin": "ಲಕ್ಕಿ ಸ್ಪಿನ್ ವೀಲ್", "spin_desc": "ದಿನಕ್ಕೊಮ್ಮೆ ತಿರುಗಿಸಿ",
        "daily_spin_badge": "ದೈನಂದಿನ ಸ್ಪಿನ್", "spin_now": "ಸ್ಪಿನ್ ಮಾಡು",
        "golden_scratch": "ಗೋಲ್ಡನ್ ಸ್ಕ್ರ್ಯಾಚ್ ಕಾರ್ಡ್", "scratch_desc": "ತಕ್ಷಣ ಬಹುಮಾನ, ದಿನಕ್ಕೆ 3 ಪ್ರಯತ್ನ",
        "three_daily": "3x ದೈನಂದಿನ", "scratch_now": "ಸ್ಕ್ರ್ಯಾಚ್ ಮಾಡು",
        "completed": "ಮುಗಿದಿದೆ", "complete_btn": "ಮುಗಿಸು", "submitting": "ಸಲ್ಲಿಸಲಾಗುತ್ತಿದೆ...",
        "submit_quiz": "ಕ್ವಿಜ್ ಸಲ್ಲಿಸು", "spinning": "ತಿರುಗುತ್ತಿದೆ...", "spin_btn": "ಸ್ಪಿನ್!",
        "scratching": "ಸ್ಕ್ರ್ಯಾಚ್ ಮಾಡಲಾಗುತ್ತಿದೆ...", "scratch_btn": "ಸ್ಕ್ರ್ಯಾಚ್!",
        "score_label": "ಸ್ಕೋರ್:", "close": "ಮುಚ್ಚಿ", "correct_of": "ರಿಂದ",
        "better_luck": "ಮುಂದಿನ ಬಾರಿ ಶುಭ!", "attempts_left": "ಪ್ರಯತ್ನಗಳು ಉಳಿದಿವೆ",
        "daily_limit_reached": "ದೈನಂದಿನ ಮಿತಿ ತಲುಪಿದೆ!", "one_spin_day": "ದಿನಕ್ಕೊಮ್ಮೆ - ಶುಭಕಾಮನೆಗಳು!",
        "scratch_reveal": "ಬಹುಮಾನ ನೋಡಲು ಸ್ಕ್ರ್ಯಾಚ್ ಮಾಡಿ!",
        "quiz_complete": "ಕ್ವಿಜ್ ಮುಗಿದಿದೆ!", "try_tomorrow": "ನಾಳೆ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ!",
        "quiz_challenge": "ಕ್ವಿಜ್ ಸವಾಲು", "answer_all": "ಎಲ್ಲಾ ಪ್ರಶ್ನೆಗಳಿಗೂ ಸರಿಯಾಗಿ ಉತ್ತರಿಸಿ",
        "spin_title": "ಚಕ್ರ ತಿರುಗಿಸಿ", "scratch_title": "ಸ್ಕ್ರ್ಯಾಚ್ ಕಾರ್ಡ್",
        "watch_ad": "ಜಾಹೀರಾತು ನೋಡು", "watching": "ನೋಡಲಾಗುತ್ತಿದೆ..."
    },
    "dashboard": {
        "your_xi": " ರ XI", "your_stats": "ನಿಮ್ಮ ಅಂಕಿ ಅಂಶಗಳು",
        "streak_label": "ಸ್ಟ್ರೀಕ್", "accuracy_label": "ನಿಖರತೆ", "xp_label": "XP",
        "progress_reward": "ಮುಂದಿನ ಬಹುಮಾನದ ಕಡೆ ಪ್ರಗತಿ",
        "unlock_skill": "ಕೌಶಲ್ಯದ ಮೂಲಕ ನಿಜ ಉತ್ಪನ್ನಗಳನ್ನು ಅನ್‌ಲಾಕ್ ಮಾಡಿ",
        "coins_available": "ಕಾಯಿನ್‌ಗಳು ಲಭ್ಯ", "halfway": "ಅರ್ಧ ದಾರಿ ಬಂದಿದೆ!",
        "almost_unlocked": "ಬಹುತೇಕ ಅನ್‌ಲಾಕ್!", "ready_claim": "ಕ್ಲೈಮ್ ಮಾಡಲು ಸಿದ್ಧ!",
        "complete_pct": "% ಮುಗಿದಿದೆ", "coins_to_go": "ಕಾಯಿನ್‌ಗಳು ಬೇಕು",
        "ready_redeem": "ರಿಡೀಮ್ ಮಾಡಲು ಸಿದ್ಧ!", "earn_more_btn": "ಹೆಚ್ಚು ಗಳಿಸಿ",
        "redeem_btn": "ರಿಡೀಮ್", "start_earning": "ಬಹುಮಾನ ಅನ್‌ಲಾಕ್ ಮಾಡಲು ಗಳಿಸಲು ಪ್ರಾರಂಭಿಸಿ!",
        "live_cricket": "ಲೈವ್ ಕ್ರಿಕೆಟ್ ಊಹೆ", "live_now_badge": "ಈಗ ಲೈವ್",
        "predict_ball": "ಕಾಯಿನ್‌ಗಳು ಗಳಿಸಲು ಚೆಂಡಿನ ಫಲಿತಾಂಶಗಳನ್ನು ಊಹಿಸಿ",
        "earn_per_correct": "ಸರಿಯಾದ ಊಹೆಗೆ 5-15 ಕಾಯಿನ್‌ಗಳು",
        "ipl_coming": "T20 ಸೀಸನ್ 2026 ಮಾರ್ಚ್ 26 ರಿಂದ",
        "get_ready": "ಲೈವ್ ಚೆಂಡು-ಚೆಂಡಾಗಿ ಊಹೆಗಳಿಗೆ ಸಿದ್ಧರಾಗಿ!",
        "view_upcoming": "ಮುಂಬರುವ ಮ್ಯಾಚ್‌ಗಳನ್ನು ನೋಡಿ",
        "watch_live": "ಲೈವ್ ನೋಡಿ", "view_match": "ಮ್ಯಾಚ್ ನೋಡಿ",
        "daily_checkin": "ದೈನಂದಿನ ಚೆಕ್-ಇನ್", "check_in_now": "ಈಗ ಚೆಕ್ ಇನ್ ಮಾಡಿ",
        "checking_in": "ಚೆಕ್ ಇನ್ ಆಗುತ್ತಿದೆ...", "streak_txt": "ಸ್ಟ್ರೀಕ್:",
        "days": "ದಿನಗಳು", "checked_today": "ಇಂದು ಚೆಕ್ ಇನ್ ಆಗಿದೆ!",
        "come_back_tom": "ನಾಳೆ ಬನ್ನಿ", "join_community": "ಸಮುದಾಯಕ್ಕೆ ಸೇರಿ",
        "compete_friends": "ಸ್ನೇಹಿತರೊಂದಿಗೆ ಸ್ಪರ್ಧಿಸಿ",
        "fantasy_teams": "ಫ್ಯಾಂಟಸಿ ತಂಡಗಳು", "private_leagues": "ಖಾಸಗಿ ಲೀಗ್‌ಗಳು",
        "invite_friends_lbl": "ಸ್ನೇಹಿತರನ್ನು ಆಮಂತ್ರಿಸಿ", "mini_games": "ಮಿನಿ ಆಟಗಳು",
        "up_to": "ವರೆಗೆ", "skill_leaderboard": "ಕೌಶಲ್ಯ ಲೀಡರ್‌ಬೋರ್ಡ್",
        "top_predictors": "ನಿಖರತೆಯಲ್ಲಿ ಅಗ್ರ ಊಹೆಗಾರರು",
        "start_predicting": "ಸೇರಲು ಊಹಿಸಲು ಪ್ರಾರಂಭಿಸಿ!",
        "recent_activity": "ಇತ್ತೀಚಿನ ಚಟುವಟಿಕೆ", "coin_movements": "ನಿಮ್ಮ ಕಾಯಿನ್ ಚಲನೆಗಳು",
        "no_transactions": "ವಹಿವಾಟುಗಳಿಲ್ಲ", "redeem_coins": "ನಿಮ್ಮ ಕಾಯಿನ್‌ಗಳನ್ನು ರಿಡೀಮ್ ಮಾಡಿ",
        "starting_10": "ಕೇವಲ 10 ಕಾಯಿನ್‌ಗಳಿಂದ ಪ್ರಾರಂಭ", "browse_shop": "ಅಂಗಡಿ ನೋಡಿ",
        "correct_label": "ಸರಿ", "total_label": "ಒಟ್ಟು",
        "beta_label": "ನೀವು FREE11 ಬೀಟಾದಲ್ಲಿದ್ದೀರಿ", "beta_report": "ವರದಿ",
        "balance_label": "ಬ್ಯಾಲೆನ್ಸ್", "checkin_failed": "ಚೆಕ್-ಇನ್ ವಿಫಲವಾಗಿದೆ",
        "real_goods": "ನಿಜ ಉತ್ಪನ್ನಗಳು", "welcome_back": "FREE11 ಗೆ ಸ್ವಾಗತ!",
        "quick_start": "ಊಹೆ ಮಾಡಿ, ಆಟ ಆಡಿ, FREE ಕಾಯಿನ್‌ಗಳು ಗಳಿಸಿ"
    },
    "profile_page": {
        "level": "ಮಟ್ಟ", "xp": "XP", "progress_next": "ಮುಂದಿನ ಮಟ್ಟದ ಕಡೆ ಪ್ರಗತಿ",
        "xp_needed": "XP ಬೇಕು", "max_level": "ಗರಿಷ್ಠ ಮಟ್ಟ", "your_balance": "ನಿಮ್ಮ ಬ್ಯಾಲೆನ್ಸ್",
        "redeem_btn": "ರಿಡೀಮ್", "your_stats": "ನಿಮ್ಮ ಅಂಕಿ ಅಂಶಗಳು",
        "predictions": "ಊಹೆಗಳು", "accuracy": "ನಿಖರತೆ", "total_earned": "ಒಟ್ಟು ಗಳಿಸಿದ್ದು",
        "invite_friends": "ಸ್ನೇಹಿತರನ್ನು ಆಮಂತ್ರಿಸಿ", "earn_badge": "50 ಗಳಿಸಿ",
        "my_orders": "ನನ್ನ ಆರ್ಡರ್‌ಗಳು", "earn_coins": "ಕಾಯಿನ್‌ಗಳು ಗಳಿಸಿ",
        "redeem_shop": "ಅಂಗಡಿಯಲ್ಲಿ ರಿಡೀಮ್ ಮಾಡಿ", "help_support": "ಸಹಾಯ ಮತ್ತು ಬೆಂಬಲ",
        "sound_effects": "ಶಬ್ದ ಪರಿಣಾಮಗಳು", "settings_title": "ಸೆಟ್ಟಿಂಗ್‌ಗಳು",
        "admin_dashboard": "ನಿರ್ವಾಹಕ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
        "legal_info": "ಕಾನೂನು ಮಾಹಿತಿ", "about_free11": "FREE11 ಬಗ್ಗೆ",
        "terms_conditions": "ನಿಯಮ ಮತ್ತು ಷರತ್ತುಗಳು", "privacy_policy": "ಗೌಪ್ಯತಾ ನೀತಿ",
        "community_guidelines": "ಸಮುದಾಯ ಮಾರ್ಗಸೂಚಿಗಳು", "faq": "ಸಾಮಾನ್ಯ ಪ್ರಶ್ನೆಗಳು",
        "log_out": "ಲಾಗ್ ಔಟ್", "logout_confirm_title": "ಖಚಿತವಾಗಿ?",
        "logout_message": "FREE11 ಖಾತೆ ಪ್ರವೇಶಿಸಲು ಮತ್ತೆ ಸೈನ್ ಇನ್ ಮಾಡಬೇಕಾಗುತ್ತದೆ.",
        "yes_logout": "ಹೌದು, ಲಾಗ್ ಔಟ್", "version": "FREE11 v1.0",
        "sounds_enabled_msg": "ಶಬ್ದ ಸಕ್ರಿಯಗೊಂಡಿದೆ", "sounds_disabled_msg": "ಶಬ್ದ ನಿಷ್ಕ್ರಿಯಗೊಂಡಿದೆ",
        "logged_out_msg": "ಯಶಸ್ವಿಯಾಗಿ ಲಾಗ್ ಔಟ್ ಆಗಿದ್ದೀರಿ",
        "rookie": "ಹೊಸಬ", "amateur": "ಕಡಿಮೆ ಅನುಭವಿ", "pro": "ಪ್ರೊ", "expert": "ತಜ್ಞ",
        "legend": "ದಂತಕಥೆ", "coins_label": "ಕಾಯಿನ್‌ಗಳು"
    },
    "ledger_page": {
        "title": "ಕಾಯಿನ್ ಲೆಡ್ಜರ್", "available_balance": "ಲಭ್ಯ ಬ್ಯಾಲೆನ್ಸ್",
        "all": "ಎಲ್ಲ", "credits": "ಕ್ರೆಡಿಟ್", "debits": "ಡೆಬಿಟ್",
        "no_transactions": "ವಹಿವಾಟುಗಳಿಲ್ಲ", "loading": "ಲೋಡ್ ಆಗುತ್ತಿದೆ...",
        "failed": "ಲೆಡ್ಜರ್ ಲೋಡ್ ವಿಫಲ", "ad_reward": "ಜಾಹೀರಾತು ಬಹುಮಾನ",
        "prediction_reward": "ಊಹೆ ಗೆಲುವು", "referral_reward": "ರೆಫರಲ್ ಬಹುಮಾನ",
        "referral_bonus": "ರೆಫರಲ್ ಬೋನಸ್", "contest_entry": "ಸ್ಪರ್ಧೆ ಪ್ರವೇಶ",
        "redemption": "ರಿಡೆಂಪ್ಷನ್", "admin_adjust": "ನಿರ್ವಾಹಕ ಹೊಂದಾಣಿಕೆ",
        "signup_bonus": "ಸೈನ್ಅಪ್ ಬೋನಸ್", "daily_checkin": "ದೈನಂದಿನ ಚೆಕ್-ಇನ್"
    },
    "shop_page": {
        "title": "ಅಂಗಡಿ", "subtitle": "ನಿಮ್ಮ ಉಚಿತ ಕಾಯಿನ್‌ಗಳನ್ನು ನಿಜ ಉತ್ಪನ್ನಗಳಿಗೆ ರಿಡೀಮ್ ಮಾಡಿ",
        "all_products": "ಎಲ್ಲಾ ಉತ್ಪನ್ನಗಳು", "recharge": "ರೀಚಾರ್ಜ್", "ott": "OTT",
        "food": "ಆಹಾರ", "vouchers": "ವೌಚರ್‌ಗಳು", "electronics": "ಎಲೆಕ್ಟ್ರಾನಿಕ್ಸ್",
        "fashion": "ಫ್ಯಾಷನ್", "groceries": "ದಿನಸಿ", "out_of_stock": "ಸ್ಟಾಕ್ ಇಲ್ಲ",
        "coins_away": "ಕಾಯಿನ್‌ಗಳು ಬೇಕು!", "redeem_now": "ಈಗ ರಿಡೀಮ್ ಮಾಡಿ",
        "level_required": "ಮಟ್ಟ", "required": "ಅಗತ್ಯ",
        "no_products": "ಉತ್ಪನ್ನಗಳು ಕಂಡುಬಂದಿಲ್ಲ", "try_category": "ಬೇರೆ ವರ್ಗ ಪ್ರಯತ್ನಿಸಿ",
        "confirm_redemption": "ರಿಡೆಂಪ್ಷನ್ ಖಚಿತಪಡಿಸಿ",
        "voucher_delivery": "ವೌಚರ್ ಕೋಡ್ WhatsApp ಮತ್ತು ಇಮೇಲ್ ಮೂಲಕ ಕಳುಹಿಸಲಾಗುತ್ತದೆ.",
        "mobile_delivery": "ಮೊಬೈಲ್ ಸಂಖ್ಯೆ (ವೌಚರ್ ಡೆಲಿವರಿಗಾಗಿ)",
        "your_balance": "ನಿಮ್ಮ ಬ್ಯಾಲೆನ್ಸ್", "product_cost": "ಉತ್ಪನ್ನ ವೆಚ್ಚ", "new_balance": "ಹೊಸ ಬ್ಯಾಲೆನ್ಸ್",
        "first_redemption_msg": "ಮೊದಲ ರಿಡೆಂಪ್ಷನ್! ಆನಂದಿಸಿ!",
        "confirm_btn": "ರಿಡೆಂಪ್ಷನ್ ಖಚಿತಪಡಿಸಿ", "processing": "ಪ್ರಕ್ರಿಯೆ ನಡೆಯುತ್ತಿದೆ...",
        "success_title": "ಅನ್‌ಲಾಕ್! ನಿಮ್ಮ ಬಹುಮಾನ ಸಿದ್ಧ",
        "success_sub": "ಕೌಶಲ್ಯದ ಮೂಲಕ ಗಳಿಸಿದ್ದೀರಿ. ಆನಂದಿಸಿ!",
        "delivery_progress": "ಡೆಲಿವರಿ ನಡೆಯುತ್ತಿದೆ", "continue_shopping": "ಶಾಪಿಂಗ್ ಮುಂದುವರಿಸಿ",
        "valid_mobile": "ಸರಿಯಾದ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ ನಮೂದಿಸಿ",
        "brand_funded": "ಬ್ರ್ಯಾಂಡ್-ಹಣಕಾಸಿನ", "limited_drop": "ಸೀಮಿತ",
        "stock_label": "ಸ್ಟಾಕ್:", "coins_label": "ಕಾಯಿನ್‌ಗಳು", "cancel": "ರದ್ದುಮಾಡಿ"
    },
    "footer_links": {
        "about": "ಬಗ್ಗೆ", "terms": "ನಿಯಮಗಳು", "privacy": "ಗೌಪ್ಯತೆ",
        "refund": "ಮರುಪಾವತಿ", "responsible_play": "ಜವಾಬ್ದಾರಿ ಆಟ",
        "guidelines": "ಮಾರ್ಗಸೂಚಿಗಳು", "disclaimer": "ನಿರಾಕರಣೆ",
        "wallet_info": "ವ್ಯಾಲೆಟ್ ಮಾಹಿತಿ", "faq": "FAQ", "support": "ಸಹಾಯ"
    },
    "legal": {"english_only_notice": "ಈ ದಾಖಲೆ ಪ್ರಸ್ತುತ ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ ಮಾತ್ರ ಲಭ್ಯ."},
    "landing": {
        "headline1": "ಸರಿಯಾದ ನಿರ್ಧಾರ ತೆಗೆದುಕೊಳ್ಳಿ.", "headline2": "ನಿಜ ಬಹುಮಾನ ಪಡೆಯಿರಿ.",
        "subheadline": "FREE11 - ನಿಮ್ಮ ಕ್ರೀಡಾ ಜ್ಞಾನವನ್ನು ನಿಜ ಉತ್ಪನ್ನಗಳಾಗಿ ಮಾರ್ಪಡಿಸಿ.",
        "hero_desc": "ಮ್ಯಾಚ್ ಕ್ಷಣಗಳನ್ನು ಊಹಿಸಿ, ಆಟ ಆಡಿ, ಕಾರ್ಯಗಳನ್ನು ಮುಗಿಸಿ.",
        "start_playing": "ಆಡಲು ಪ್ರಾರಂಭಿಸಿ", "explore_games": "ಆಟಗಳನ್ನು ಅನ್ವೇಷಿಸಿ",
        "start": "ಪ್ರಾರಂಭಿಸಿ", "login": "ಲಾಗಿನ್", "sign_in": "ಸೈನ್ ಇನ್",
        "platform_title": "FREE11 ನಲ್ಲಿ ಎಲ್ಲವೂ", "platform_subtitle": "ಒಂದು ವೇದಿಕೆ. ಆರು ರೀತಿಯಲ್ಲಿ ಗಳಿಸಿ.",
        "feature1_title": "ಲೈವ್ ಮ್ಯಾಚ್ ಊಹೆಗಳು", "feature1_desc": "ನಿಜ ಸಮಯದಲ್ಲಿ ಮ್ಯಾಚ್ ಕ್ಷಣಗಳನ್ನು ಊಹಿಸಿ.",
        "feature2_title": "ಕೌಶಲ್ಯ ಆಧಾರಿತ ಆಟಗಳು", "feature2_desc": "ರಮ್ಮಿ, ಪೋಕರ್, ತೀನ್ ಪಟ್ಟಿ ಆಡಿ.",
        "feature3_title": "ಮಿಷನ್‌ಗಳು & ದೈನಂದಿನ ಸವಾಲುಗಳು", "feature3_desc": "ಕಾರ್ಯಗಳು ಮುಗಿಸಿ ಕಾಯಿನ್‌ಗಳು ಗಳಿಸಿ.",
        "feature4_title": "ಲೀಡರ್‌ಬೋರ್ಡ್‌ಗಳು", "feature4_desc": "ಸ್ನೇಹಿತರೊಂದಿಗೆ ಸ್ಪರ್ಧಿಸಿ.",
        "feature5_title": "ಬಹುಮಾನ ಅಂಗಡಿ", "feature5_desc": "ಕಾಯಿನ್‌ಗಳಿಂದ ವೌಚರ್‌ಗಳು ರಿಡೀಮ್ ಮಾಡಿ.",
        "feature6_title": "FREE Bucks", "feature6_desc": "ಪ್ರೀಮಿಯಂ ಸ್ಪರ್ಧೆಗಳನ್ನು ಅನ್‌ಲಾಕ್ ಮಾಡಿ.",
        "how_it_works": "ಇದು ಹೇಗೆ ಕಾರ್ಯ ನಿರ್ವಹಿಸುತ್ತದೆ",
        "step1_title": "ಖಾತೆ ರಚಿಸಿ", "step1_desc": "60 ಸೆಕೆಂಡ್‌ಗಳಲ್ಲಿ ಉಚಿತ ಸೈನ್‌ಅಪ್",
        "step2_title": "ಆಡಿ & ಊಹಿಸಿ", "step2_desc": "ಮ್ಯಾಚ್ ಊಹಿಸಿ, ಆಟ ಆಡಿ",
        "step3_title": "ಕಾಯಿನ್‌ಗಳು ಗಳಿಸಿ", "step3_desc": "ಪ್ರತಿ ಸರಿಯಾದ ಊಹೆ ಕಾಯಿನ್‌ಗಳು ತರುತ್ತದೆ",
        "step4_title": "ಉತ್ಪನ್ನಗಳು ಪಡೆಯಿರಿ", "step4_desc": "ಕಾಯಿನ್‌ಗಳಿಂದ ನಿಜ ಉತ್ಪನ್ನಗಳು ರಿಡೀಮ್ ಮಾಡಿ",
        "cta_headline": "ಇಂದೇ FREE11 ಪ್ರಯಾಣ ಪ್ರಾರಂಭಿಸಿ.",
        "cta_desc": "ಸಾವಿರಾರು ಕ್ರೀಡಾ ಅಭಿಮಾನಿಗಳೊಂದಿಗೆ ಸೇರಿ.",
        "create_account": "ಖಾತೆ ರಚಿಸಿ", "login_btn": "ಲಾಗಿನ್",
        "disclaimer_title": "ಹಕ್ಕು ನಿರಾಕರಣ:", "disclaimer_text": "FREE11 ಕೌಶಲ್ಯ ಆಧಾರಿತ ವೇದಿಕೆ. ಜೂಜಾಟ ಅಲ್ಲ. 18+ ಮಾತ್ರ.",
        "tagline_coins": "ಕೌಶಲ್ಯ → ಕಾಯಿನ್‌ಗಳು → ನಿಜ ಉತ್ಪನ್ನಗಳು",
        "copyright_suffix": "ನಿಮ್ಮ ಜ್ಞಾನ, ನಿಜ ಬಹುಮಾನಗಳು"
    },
    "leaderboard_page": {
        "title": "ಲೀಡರ್‌ಬೋರ್ಡ್‌ಗಳು", "subtitle": "ಕೌಶಲ್ಯದಲ್ಲಿ ಸ್ಪರ್ಧಿಸಿ!",
        "loading": "ಲೀಡರ್‌ಬೋರ್ಡ್‌ಗಳು ಲೋಡ್ ಆಗುತ್ತಿವೆ...", "global_tab": "ಜಾಗತಿಕ",
        "weekly_tab": "ಸಾಪ್ತಾಹಿಕ", "streak_tab": "ಸ್ಟ್ರೀಕ್‌ಗಳು",
        "global_title": "ಜಾಗತಿಕ ಶ್ರೇಣಿಗಳು", "global_desc": "ಸರ್ವಕಾಲ ಊಹೆ ನಿಖರತೆ",
        "weekly_title": "ಸಾಪ್ತಾಹಿಕ ಶ್ರೇಣಿಗಳು", "weekly_desc": "ಈ ವಾರದ ಅಗ್ರ ಊಹೆಗಾರರು",
        "streak_title": "ಸ್ಟ್ರೀಕ್ ಕಿಂಗ್ಸ್", "streak_desc": "ಸತತ ಸರಿಯಾದ ಊಹೆಗಳು",
        "no_global": "ಇನ್ನೂ ಶ್ರೇಣಿಗಳಿಲ್ಲ.", "no_weekly": "ಈ ವಾರ ಊಹೆಗಳಿಲ್ಲ.", "no_streak": "ಸ್ಟ್ರೀಕ್‌ಗಳಿಲ್ಲ.",
        "duels_title": "ಊಹೆ ದ್ವಂದ್ವಗಳು", "duels_desc": "ಸ್ನೇಹಿತರನ್ನು ಸವಾಲು ಮಾಡಿ!",
        "activity_title": "ಚಟುವಟಿಕೆ ಫೀಡ್",
        "incoming_challenges": "ಬರುತ್ತಿರುವ ಸವಾಲುಗಳು", "active_duels": "ಸಕ್ರಿಯ ದ್ವಂದ್ವಗಳು",
        "no_duels": "ದ್ವಂದ್ವಗಳಿಲ್ಲ.", "no_activity": "ಇತ್ತೀಚಿನ ಚಟುವಟಿಕೆಗಳಿಲ್ಲ",
        "challenged_you": "ನಿಮ್ಮನ್ನು ಸವಾಲು ಮಾಡಿದ್ದಾರೆ!",
        "accept": "ಒಪ್ಪಿಕೊಳ್ಳಿ", "decline": "ತಿರಸ್ಕರಿಸಿ", "challenge_btn": "ದ್ವಂದ್ವಕ್ಕೆ ಸವಾಲು ಮಾಡಿ",
        "won": "ಗೆದ್ದದ್ದು", "played": "ಆಡಿದ್ದು", "win_rate": "ಗೆಲುವಿನ ದರ",
        "you": "ನೀವು:", "them": "ಅವರು:", "accuracy_pct": "ನಿಖರತೆ", "correct_label": "ಸರಿ"
    },
    "referrals_page": {
        "title": "ರೆಫರ್ ಮಾಡಿ & ಗಳಿಸಿ", "your_code": "ನಿಮ್ಮ ರೆಫರಲ್ ಕೋಡ್",
        "share_msg": "ಈ ಕೋಡ್ ಅನ್ನು ಸ್ನೇಹಿತರೊಂದಿಗೆ ಹಂಚಿಕೊಳ್ಳಿ. ಇಬ್ಬರೂ ಕಾಯಿನ್‌ಗಳು ಗಳಿಸುತ್ತಾರೆ!",
        "referrals_label": "ರೆಫರಲ್‌ಗಳು", "earned_label": "ಗಳಿಸಿದ್ದು", "per_invite_label": "ಆಮಂತ್ರಣಕ್ಕೆ",
        "have_code": "ರೆಫರಲ್ ಕೋಡ್ ಇದೆಯೇ?", "enter_code": "ಕೋಡ್ ನಮೂದಿಸಿ",
        "apply": "ಅನ್ವಯಿಸಿ", "how_it_works": "ಇದು ಹೇಗೆ ಕಾರ್ಯ ನಿರ್ವಹಿಸುತ್ತದೆ",
        "step1": "ನಿಮ್ಮ ಅನನ್ಯ ಕೋಡ್ ಸ್ನೇಹಿತರೊಂದಿಗೆ ಹಂಚಿ",
        "step2": "ಸ್ನೇಹಿತ ನಮೂದಿಸಿ ನಿಮ್ಮ ಕೋಡ್ ಹಾಕುತ್ತಾರೆ",
        "step3_prefix": "ನೀವು ಪಡೆಯುತ್ತೀರಿ", "step3_suffix": "ಕಾಯಿನ್‌ಗಳು, ಸ್ನೇಹಿತ 25 ಕಾಯಿನ್‌ಗಳು"
    },
    "cardgames_page": {
        "select_game": "ಆಟ ಆಯ್ಕೆ ಮಾಡಿ", "available_rooms": "ಲಭ್ಯ ಕೊಠಡಿಗಳು",
        "active_games": "ನಿಮ್ಮ ಸಕ್ರಿಯ ಆಟಗಳು", "join_code": "ಖಾಸಗಿ ಕೊಠಡಿಗೆ ಸೇರಿ",
        "enter_code": "ಕೊಠಡಿ ಕೋಡ್ ನಮೂದಿಸಿ", "join": "ಸೇರಿ", "no_rooms": "ಕೊಠಡಿಗಳಿಲ್ಲ",
        "create_room": "ಕೊಠಡಿ ರಚಿಸಿ", "join_by_code": "ಕೋಡ್‌ನಿಂದ ಸೇರಿ",
        "loading": "ಲೋಡ್ ಆಗುತ್ತಿದೆ...", "copy_code": "ನಕಲು", "invite_friend": "ಸ್ನೇಹಿತನನ್ನು ಆಮಂತ್ರಿಸಿ",
        "how_it_works": "ಇದು ಹೇಗೆ ಕಾರ್ಯ ನಿರ್ವಹಿಸುತ್ತದೆ",
        "step1": "ಒಂದು ಆಟ ಆಯ್ಕೆ ಮಾಡಿ", "step2": "ಕೊಠಡಿಗೆ ಸೇರಿ ಅಥವಾ ರಚಿಸಿ", "step3": "ಆಡಿ & ಗಳಿಸಿ"
    },
    "support_page": {
        "title": "ಸಹಾಯ & ಬೆಂಬಲ", "chat_tab": "ಚಾಟ್", "tickets_tab": "ಟಿಕೆಟ್‌ಗಳು",
        "type_message": "ಸಂದೇಶ ಟೈಪ್ ಮಾಡಿ...", "send": "ಕಳುಹಿಸಿ",
        "create_ticket": "ಟಿಕೆಟ್ ರಚಿಸಿ", "no_tickets": "ಟಿಕೆಟ್‌ಗಳಿಲ್ಲ",
        "loading": "ಲೋಡ್ ಆಗುತ್ತಿದೆ..."
    },
    "notifications": {
        "title": "ಅಧಿಸೂಚನೆಗಳು", "enable": "ಅಧಿಸೂಚನೆಗಳನ್ನು ಸಕ್ರಿಯಗೊಳಿಸಿ",
        "settings": "ಅಧಿಸೂಚನೆ ಸೆಟ್ಟಿಂಗ್‌ಗಳು"
    }
}

# Marathi (mr) — reuse Kannada structure with Marathi text
MISSING["mr"] = {k: {} for k in MISSING["kn"]}
MISSING["mr"]["earn_page"] = {
    "title": "कॉइन बूस्टर", "subtitle": "बोनस क्रियाकलापांद्वारे कमाई वाढवा",
    "supplementary": "हे क्रिकेट अंदाजांना पूरक आहेत", "how_to_earn": "कसे कमवायचे",
    "mini_games_tab": "मिनी गेम्स", "tasks_tab": "कार्ये",
    "fantasy_contests": "फँटसी स्पर्धा", "fantasy_desc": "स्वप्नातील संघ बनवा आणि स्पर्धा करा.",
    "up_to_500": "प्रति स्पर्धेत 500 कॉइन पर्यंत",
    "match_winner": "मॅच विजेता अंदाज", "match_winner_desc": "जिंकणाऱ्या संघाचा अंदाज करा.",
    "fifty_per": "बरोबर अंदाजासाठी 50 कॉइन",
    "over_outcome": "ओव्हर परिणाम अंदाज", "over_desc": "थेट सामन्यांमध्ये धावांचा अंदाज करा.",
    "twenty_five": "बरोबर अंदाजासाठी 25 कॉइन",
    "ball_by_ball": "चेंडू-चेंडू", "ball_desc": "डिलिव्हरी परिणामांचा अंदाज करा.",
    "five_fifteen": "बरोबर अंदाजासाठी 5-15 कॉइन",
    "mini_tasks": "मिनी गेम्स आणि कार्ये", "mini_desc": "दैनंदिन गेम्स खेळा.",
    "ten_hundred": "क्रियाकलापासाठी 10-100 कॉइन",
    "quiz_title": "क्रिकेट क्विझ आव्हान", "quiz_desc": "तुमचे क्रिकेट ज्ञान तपासा",
    "up_to_50": "50 कॉइन पर्यंत", "play_now": "आता खेळा",
    "lucky_spin": "लकी स्पिन व्हील", "spin_desc": "दिवसातून एकदा फिरवा",
    "daily_spin_badge": "दैनंदिन स्पिन", "spin_now": "स्पिन करा",
    "golden_scratch": "गोल्डन स्क्रॅच कार्ड", "scratch_desc": "तात्काळ बक्षीस, दिवसाला 3 प्रयत्न",
    "three_daily": "3x दैनंदिन", "scratch_now": "स्क्रॅच करा",
    "completed": "पूर्ण झाले", "complete_btn": "पूर्ण करा", "submitting": "सादर करत आहे...",
    "submit_quiz": "क्विझ सादर करा", "spinning": "फिरत आहे...", "spin_btn": "स्पिन!",
    "scratching": "स्क्रॅच होत आहे...", "scratch_btn": "स्क्रॅच!",
    "score_label": "गुण:", "close": "बंद करा", "correct_of": "पैकी",
    "better_luck": "पुढच्या वेळी शुभेच्छा!", "attempts_left": "प्रयत्न शिल्लक",
    "daily_limit_reached": "दैनंदिन मर्यादा गाठली!", "one_spin_day": "दिवसाला एक स्पिन - शुभेच्छा!",
    "scratch_reveal": "बक्षीस पाहण्यासाठी स्क्रॅच करा!",
    "quiz_complete": "क्विझ पूर्ण!", "try_tomorrow": "उद्या पुन्हा प्रयत्न करा!",
    "quiz_challenge": "क्विझ आव्हान", "answer_all": "जास्त कॉइनसाठी सर्व प्रश्नांची उत्तरे द्या",
    "spin_title": "चाक फिरवा", "scratch_title": "स्क्रॅच कार्ड",
    "watch_ad": "जाहिरात पाहा", "watching": "पाहत आहे..."
}
MISSING["mr"]["dashboard"] = {
    "your_xi": " चे XI", "your_stats": "तुमचे आकडेवारी",
    "streak_label": "स्ट्रीक", "accuracy_label": "अचूकता", "xp_label": "XP",
    "progress_reward": "पुढील बक्षीसाकडे प्रगती",
    "unlock_skill": "कौशल्याद्वारे खरे उत्पादन अनलॉक करा",
    "coins_available": "कॉइन उपलब्ध", "halfway": "अर्धे झाले!",
    "almost_unlocked": "जवळजवळ अनलॉक!", "ready_claim": "दावा करण्यास तयार!",
    "complete_pct": "% पूर्ण", "coins_to_go": "कॉइन हवेत",
    "ready_redeem": "रिडीम करण्यास तयार!", "earn_more_btn": "अधिक कमवा",
    "redeem_btn": "रिडीम करा", "start_earning": "बक्षीस अनलॉक करण्यासाठी कमवायला सुरुवात करा!",
    "live_cricket": "थेट क्रिकेट अंदाज", "live_now_badge": "आता थेट",
    "predict_ball": "कॉइन कमवण्यासाठी चेंडूचे परिणाम अंदाज करा",
    "earn_per_correct": "बरोबर अंदाजासाठी 5-15 कॉइन",
    "ipl_coming": "T20 सीझन 2026 मार्च 26 पासून",
    "get_ready": "थेट चेंडू-चेंडू अंदाजासाठी तयार राहा!",
    "view_upcoming": "आगामी सामने पाहा",
    "watch_live": "थेट पाहा", "view_match": "सामना पाहा",
    "daily_checkin": "दैनंदिन चेक-इन", "check_in_now": "आता चेक इन करा",
    "checking_in": "चेक इन होत आहे...", "streak_txt": "स्ट्रीक:",
    "days": "दिवस", "checked_today": "आज चेक इन झाले!",
    "come_back_tom": "उद्या परत या", "join_community": "समुदायात सामील व्हा",
    "compete_friends": "मित्रांशी स्पर्धा करा",
    "fantasy_teams": "फँटसी संघ", "private_leagues": "खासगी लीग",
    "invite_friends_lbl": "मित्रांना आमंत्रण द्या", "mini_games": "मिनी गेम्स",
    "up_to": "पर्यंत", "skill_leaderboard": "कौशल्य लीडरबोर्ड",
    "top_predictors": "अचूकतेत शीर्ष अंदाजकर्ते",
    "start_predicting": "सामील होण्यासाठी अंदाज करायला सुरुवात करा!",
    "recent_activity": "अलीकडील क्रियाकलाप", "coin_movements": "तुमच्या कॉइनची हालचाल",
    "no_transactions": "व्यवहार नाहीत", "redeem_coins": "तुमचे कॉइन रिडीम करा",
    "starting_10": "फक्त 10 कॉइनपासून सुरुवात", "browse_shop": "दुकान पाहा",
    "correct_label": "बरोबर", "total_label": "एकूण",
    "beta_label": "तुम्ही FREE11 बीटामध्ये आहात", "beta_report": "अहवाल",
    "balance_label": "शिल्लक", "checkin_failed": "चेक-इन अयशस्वी",
    "real_goods": "खरी उत्पादने", "welcome_back": "FREE11 मध्ये स्वागत!",
    "quick_start": "अंदाज करा, गेम खेळा, FREE कॉइन कमवा"
}
MISSING["mr"]["profile_page"] = {
    "level": "स्तर", "xp": "XP", "progress_next": "पुढील स्तराकडे प्रगती",
    "xp_needed": "XP हवे", "max_level": "कमाल स्तर", "your_balance": "तुमची शिल्लक",
    "redeem_btn": "रिडीम करा", "your_stats": "तुमची आकडेवारी",
    "predictions": "अंदाज", "accuracy": "अचूकता", "total_earned": "एकूण कमावले",
    "invite_friends": "मित्रांना आमंत्रण द्या", "earn_badge": "50 कमवा",
    "my_orders": "माझे ऑर्डर", "earn_coins": "कॉइन कमवा",
    "redeem_shop": "दुकानात रिडीम करा", "help_support": "मदत आणि समर्थन",
    "sound_effects": "आवाज परिणाम", "settings_title": "सेटिंग्ज",
    "admin_dashboard": "प्रशासक डॅशबोर्ड",
    "legal_info": "कायदेशीर माहिती", "about_free11": "FREE11 बद्दल",
    "terms_conditions": "नियम आणि अटी", "privacy_policy": "गोपनीयता धोरण",
    "community_guidelines": "समुदाय मार्गदर्शक तत्त्वे", "faq": "वारंवार विचारले जाणारे प्रश्न",
    "log_out": "लॉग आउट", "logout_confirm_title": "खात्री आहे का?",
    "logout_message": "FREE11 खाते ऍक्सेस करण्यासाठी पुन्हा साइन इन करावे लागेल.",
    "yes_logout": "हो, लॉग आउट", "version": "FREE11 v1.0",
    "sounds_enabled_msg": "आवाज सक्षम", "sounds_disabled_msg": "आवाज अक्षम",
    "logged_out_msg": "यशस्वीरीत्या लॉग आउट झालात",
    "rookie": "नवखा", "amateur": "हौशी", "pro": "प्रो", "expert": "तज्ञ",
    "legend": "दंतकथा", "coins_label": "कॉइन"
}
MISSING["mr"]["ledger_page"] = {
    "title": "कॉइन लेजर", "available_balance": "उपलब्ध शिल्लक",
    "all": "सर्व", "credits": "क्रेडिट", "debits": "डेबिट",
    "no_transactions": "व्यवहार नाहीत", "loading": "लोड होत आहे...",
    "failed": "लेजर लोड अयशस्वी", "ad_reward": "जाहिरात बक्षीस",
    "prediction_reward": "अंदाज विजय", "referral_reward": "रेफरल बक्षीस",
    "referral_bonus": "रेफरल बोनस", "contest_entry": "स्पर्धा प्रवेश",
    "redemption": "रिडेम्पशन", "admin_adjust": "प्रशासक समायोजन",
    "signup_bonus": "साइनअप बोनस", "daily_checkin": "दैनंदिन चेक-इन"
}
MISSING["mr"]["shop_page"] = {
    "title": "दुकान", "subtitle": "तुमचे Free कॉइन खऱ्या उत्पादनांसाठी रिडीम करा",
    "all_products": "सर्व उत्पादने", "recharge": "रिचार्ज", "ott": "OTT",
    "food": "खाद्यपदार्थ", "vouchers": "व्हाउचर", "electronics": "इलेक्ट्रॉनिक्स",
    "fashion": "फॅशन", "groceries": "किराणा", "out_of_stock": "स्टॉक नाही",
    "coins_away": "कॉइन हवेत!", "redeem_now": "आता रिडीम करा",
    "level_required": "स्तर", "required": "आवश्यक",
    "no_products": "उत्पादने आढळली नाहीत", "try_category": "वेगळी श्रेणी वापरून पाहा",
    "confirm_redemption": "रिडेम्पशन पुष्टी करा",
    "voucher_delivery": "व्हाउचर कोड WhatsApp आणि ईमेलद्वारे पाठवला जाईल.",
    "mobile_delivery": "मोबाइल नंबर (व्हाउचर डिलिव्हरीसाठी)",
    "your_balance": "तुमची शिल्लक", "product_cost": "उत्पादन किंमत", "new_balance": "नवीन शिल्लक",
    "first_redemption_msg": "पहिले रिडेम्पशन! आनंद घ्या!",
    "confirm_btn": "रिडेम्पशन पुष्टी करा", "processing": "प्रक्रिया होत आहे...",
    "success_title": "अनलॉक! तुमचे बक्षीस तयार",
    "success_sub": "कौशल्याने कमावले. आनंद घ्या!",
    "delivery_progress": "डिलिव्हरी सुरू आहे", "continue_shopping": "खरेदी सुरू ठेवा",
    "valid_mobile": "वैध मोबाइल नंबर प्रविष्ट करा",
    "brand_funded": "ब्रँड-अनुदानित", "limited_drop": "मर्यादित",
    "stock_label": "स्टॉक:", "coins_label": "कॉइन", "cancel": "रद्द करा"
}
MISSING["mr"]["footer_links"] = {
    "about": "बद्दल", "terms": "अटी", "privacy": "गोपनीयता",
    "refund": "परतावा", "responsible_play": "जबाबदार खेळ",
    "guidelines": "मार्गदर्शक तत्त्वे", "disclaimer": "अस्वीकरण",
    "wallet_info": "वॉलेट माहिती", "faq": "FAQ", "support": "समर्थन"
}
MISSING["mr"]["legal"] = {"english_only_notice": "हे दस्तऐवज सध्या फक्त इंग्रजीत उपलब्ध आहे."}
MISSING["mr"]["landing"] = {
    "headline1": "योग्य निर्णय घ्या.", "headline2": "खरे बक्षीस मिळवा.",
    "subheadline": "FREE11 - तुमचे क्रीडा ज्ञान खऱ्या उत्पादनांमध्ये रूपांतरित करा.",
    "hero_desc": "सामन्यांचा अंदाज करा, खेळा, मिशन पूर्ण करा.",
    "start_playing": "खेळणे सुरू करा", "explore_games": "गेम्स एक्सप्लोर करा",
    "start": "सुरू करा", "login": "लॉगिन", "sign_in": "साइन इन",
    "platform_title": "FREE11 वर सर्व काही", "platform_subtitle": "एक व्यासपीठ. सहा मार्गांनी कमवा.",
    "feature1_title": "थेट सामना अंदाज", "feature1_desc": "वास्तविक वेळात सामना क्षण अंदाज करा.",
    "feature2_title": "कौशल्य-आधारित गेम्स", "feature2_desc": "रम्मी, पोकर, तीन पत्ती खेळा.",
    "feature3_title": "मिशन आणि दैनंदिन आव्हाने", "feature3_desc": "कार्ये पूर्ण करून कॉइन कमवा.",
    "feature4_title": "लीडरबोर्ड", "feature4_desc": "मित्रांशी स्पर्धा करा.",
    "feature5_title": "बक्षीस दुकान", "feature5_desc": "कॉइनने व्हाउचर रिडीम करा.",
    "feature6_title": "FREE Bucks", "feature6_desc": "प्रीमियम स्पर्धा अनलॉक करा.",
    "how_it_works": "हे कसे काम करते",
    "step1_title": "खाते तयार करा", "step1_desc": "60 सेकंदात विनामूल्य साइन अप करा",
    "step2_title": "खेळा आणि अंदाज करा", "step2_desc": "सामने अंदाज करा, गेम्स खेळा",
    "step3_title": "कॉइन कमवा", "step3_desc": "प्रत्येक बरोबर अंदाज कॉइन मिळवून देतो",
    "step4_title": "उत्पादने मिळवा", "step4_desc": "कॉइनने खरी उत्पादने रिडीम करा",
    "cta_headline": "आजच FREE11 प्रवास सुरू करा.",
    "cta_desc": "हजारो क्रीडा चाहत्यांसोबत सामील व्हा.",
    "create_account": "खाते तयार करा", "login_btn": "लॉगिन",
    "disclaimer_title": "अस्वीकरण:", "disclaimer_text": "FREE11 कौशल्य-आधारित व्यासपीठ आहे. हे जुगार नाही. फक्त 18+.",
    "tagline_coins": "कौशल्य → कॉइन → खरी उत्पादने",
    "copyright_suffix": "तुमचे ज्ञान, खरे बक्षीस"
}
MISSING["mr"]["leaderboard_page"] = {
    "title": "लीडरबोर्ड", "subtitle": "कौशल्यात स्पर्धा करा!",
    "loading": "लीडरबोर्ड लोड होत आहे...", "global_tab": "जागतिक",
    "weekly_tab": "साप्ताहिक", "streak_tab": "स्ट्रीक",
    "global_title": "जागतिक रँकिंग", "global_desc": "सर्व काळातील अंदाज अचूकता",
    "weekly_title": "साप्ताहिक रँकिंग", "weekly_desc": "या आठवड्यातील शीर्ष अंदाजकर्ते",
    "streak_title": "स्ट्रीक किंग्ज", "streak_desc": "सतत बरोबर अंदाज",
    "no_global": "अद्याप रँकिंग नाही.", "no_weekly": "या आठवड्यात अंदाज नाही.", "no_streak": "स्ट्रीक नाही.",
    "duels_title": "अंदाज द्वंद्व", "duels_desc": "मित्रांना आव्हान द्या!",
    "activity_title": "क्रियाकलाप फीड",
    "incoming_challenges": "येणारी आव्हाने", "active_duels": "सक्रिय द्वंद्व",
    "no_duels": "द्वंद्व नाही.", "no_activity": "अलीकडील क्रियाकलाप नाही",
    "challenged_you": "तुम्हाला आव्हान दिले!",
    "accept": "स्वीकारा", "decline": "नाकारा", "challenge_btn": "द्वंद्वासाठी आव्हान द्या",
    "won": "जिंकले", "played": "खेळले", "win_rate": "जिंकण्याचा दर",
    "you": "तुम्ही:", "them": "ते:", "accuracy_pct": "अचूकता", "correct_label": "बरोबर"
}
MISSING["mr"]["referrals_page"] = {
    "title": "रेफर करा आणि कमवा", "your_code": "तुमचा रेफरल कोड",
    "share_msg": "हा कोड मित्रांसोबत शेअर करा. दोघेही कॉइन कमवतील!",
    "referrals_label": "रेफरल", "earned_label": "कमावले", "per_invite_label": "प्रति आमंत्रण",
    "have_code": "रेफरल कोड आहे का?", "enter_code": "कोड टाका",
    "apply": "लागू करा", "how_it_works": "हे कसे काम करते",
    "step1": "तुमचा अनन्य कोड मित्रांसोबत शेअर करा",
    "step2": "मित्र साइन अप करून तुमचा कोड टाकतो",
    "step3_prefix": "तुम्हाला मिळतात", "step3_suffix": "कॉइन, मित्राला 25 कॉइन"
}
MISSING["mr"]["cardgames_page"] = {
    "select_game": "गेम निवडा", "available_rooms": "उपलब्ध खोल्या",
    "active_games": "तुमचे सक्रिय गेम्स", "join_code": "खासगी खोलीत सामील व्हा",
    "enter_code": "खोली कोड प्रविष्ट करा", "join": "सामील व्हा", "no_rooms": "खोल्या उपलब्ध नाहीत",
    "create_room": "खोली तयार करा", "join_by_code": "कोडने सामील व्हा",
    "loading": "लोड होत आहे...", "copy_code": "कॉपी", "invite_friend": "मित्राला आमंत्रण द्या",
    "how_it_works": "हे कसे काम करते",
    "step1": "एक गेम निवडा", "step2": "खोलीत सामील व्हा किंवा तयार करा", "step3": "खेळा आणि कमवा"
}
MISSING["mr"]["support_page"] = {
    "title": "मदत आणि समर्थन", "chat_tab": "चॅट", "tickets_tab": "तिकीट",
    "type_message": "संदेश टाइप करा...", "send": "पाठवा",
    "create_ticket": "तिकीट तयार करा", "no_tickets": "तिकीट नाहीत",
    "loading": "लोड होत आहे..."
}
MISSING["mr"]["notifications"] = {
    "title": "सूचना", "enable": "सूचना सक्षम करा", "settings": "सूचना सेटिंग्ज"
}

# Malayalam (ml)
MISSING["ml"] = {k: {} for k in MISSING["kn"]}
MISSING["ml"]["earn_page"] = {
    "title": "കോയിൻ ബൂസ്റ്ററുകൾ", "subtitle": "ബോണസ് പ്രവർത്തനങ്ങൾ വഴി വരുമാനം ത്വരിതപ്പെടുത്തുക",
    "supplementary": "ഇവ ക്രിക്കറ്റ് പ്രവചനങ്ങൾക്ക് അനുബന്ധമാണ്", "how_to_earn": "എങ്ങനെ സമ്പാദിക്കാം",
    "mini_games_tab": "മിനി ഗെയിമുകൾ", "tasks_tab": "ടാസ്ക്കുകൾ",
    "fantasy_contests": "ഫാന്റസി മത്സരങ്ങൾ", "fantasy_desc": "ഡ്രീം ടീം ഉണ്ടാക്കി മത്സരിക്കുക.",
    "up_to_500": "ഒരു മത്സരത്തിന് 500 കോയിൻ വരെ",
    "match_winner": "മ്യാച്ച് വിജയി പ്രവചനം", "match_winner_desc": "ജയിക്കുന്ന ടീം ആരെന്ന് പ്രവചിക്കുക.",
    "fifty_per": "ശരിയായ പ്രവചനത്തിന് 50 കോയിൻ",
    "over_outcome": "ഓവർ ഫലം പ്രവചനം", "over_desc": "ലൈവ് മ്യാച്ചിൽ റൺ പ്രവചിക്കുക.",
    "twenty_five": "ശരിയായ പ്രവചനത്തിന് 25 കോയിൻ",
    "ball_by_ball": "ബോൾ-ബൈ-ബോൾ", "ball_desc": "ഡെലിവറി ഫലം പ്രവചിക്കുക.",
    "five_fifteen": "ശരിയായ പ്രവചനത്തിന് 5-15 കോയിൻ",
    "mini_tasks": "മിനി ഗെയിമുകളും ടാസ്ക്കുകളും", "mini_desc": "ദൈനംദിന ഗെയിമുകൾ കളിക്കുക.",
    "ten_hundred": "ഒരു പ്രവർത്തനത്തിന് 10-100 കോയിൻ",
    "quiz_title": "ക്രിക്കറ്റ് ക്വിസ് ചലഞ്ച്", "quiz_desc": "നിങ്ങളുടെ ക്രിക്കറ്റ് അറിവ് പരീക്ഷിക്കുക",
    "up_to_50": "50 കോയിൻ വരെ", "play_now": "ഇപ്പോൾ കളിക്കുക",
    "lucky_spin": "ലക്കി സ്പിൻ വീൽ", "spin_desc": "ദിവസത്തിൽ ഒരിക്കൽ തിരിക്കുക",
    "daily_spin_badge": "ദൈനംദിന സ്പിൻ", "spin_now": "സ്പിൻ ചെയ്യുക",
    "golden_scratch": "ഗോൾഡൻ സ്ക്രാച്ച് കാർഡ്", "scratch_desc": "തൽക്ഷണ സമ്മാനം, ദിവസം 3 ശ്രമം",
    "three_daily": "3x ദൈനംദിന", "scratch_now": "സ്ക്രാച്ച് ചെയ്യുക",
    "completed": "പൂർത്തിയായി", "complete_btn": "പൂർത്തിയാക്കുക", "submitting": "സമർപ്പിക്കുന്നു...",
    "submit_quiz": "ക്വിസ് സമർപ്പിക്കുക", "spinning": "തിരിയുന്നു...", "spin_btn": "സ്പിൻ!",
    "scratching": "സ്ക്രാച്ച് ചെയ്യുന്നു...", "scratch_btn": "സ്ക്രാച്ച്!",
    "score_label": "സ്കോർ:", "close": "അടക്കുക", "correct_of": "ൽ നിന്ന്",
    "better_luck": "അടുത്ത തവണ ഭാഗ്യം!", "attempts_left": "ശ്രമങ്ങൾ ബാക്കി",
    "daily_limit_reached": "ദൈനംദിന പരിധി എത്തി!", "one_spin_day": "ദിവസം ഒരു സ്പിൻ - ആശംസകൾ!",
    "scratch_reveal": "സമ്മാനം കാണാൻ സ്ക്രാച്ച് ചെയ്യുക!",
    "quiz_complete": "ക്വിസ് പൂർത്തി!", "try_tomorrow": "നാളെ വീണ്ടും ശ്രമിക്കുക!",
    "quiz_challenge": "ക്വിസ് ചലഞ്ച്", "answer_all": "കൂടുതൽ കോയിനുകൾക്ക് എല്ലാ ചോദ്യങ്ങൾക്കും ഉത്തരം നൽകുക",
    "spin_title": "ചക്രം തിരിക്കുക", "scratch_title": "സ്ക്രാച്ച് കാർഡ്",
    "watch_ad": "പരസ്യം കാണുക", "watching": "കാണുന്നു..."
}
MISSING["ml"]["dashboard"] = {
    "your_xi": " ഉടെ XI", "your_stats": "നിങ്ങളുടെ സ്ഥിതിവിവരക്കണക്കുകൾ",
    "streak_label": "സ്ട്രീക്ക്", "accuracy_label": "കൃത്യത", "xp_label": "XP",
    "progress_reward": "അടുത്ത പ്രതിഫലത്തിലേക്കുള്ള പുരോഗതി",
    "unlock_skill": "കഴിവിലൂടെ യഥാർത്ഥ ഉൽപ്പന്നങ്ങൾ അൺലോക്ക് ചെയ്യുക",
    "coins_available": "കോയിൻ ലഭ്യമാണ്", "halfway": "പകുതി വഴി!",
    "almost_unlocked": "ഏതാണ്ട് അൺലോക്ക്!", "ready_claim": "ക്ലെയിം ചെയ്യാൻ തയ്യാർ!",
    "complete_pct": "% പൂർത്തി", "coins_to_go": "കോയിൻ വേണം",
    "ready_redeem": "റിഡീം ചെയ്യാൻ തയ്യാർ!", "earn_more_btn": "കൂടുതൽ സമ്പാദിക്കുക",
    "redeem_btn": "റിഡീം ചെയ്യുക", "start_earning": "പ്രതിഫലം അൺലോക്ക് ചെയ്യാൻ സമ്പാദിക്കൂ!",
    "live_cricket": "ലൈവ് ക്രിക്കറ്റ് പ്രവചനം", "live_now_badge": "ഇപ്പോൾ ലൈവ്",
    "predict_ball": "കോയിൻ സമ്പാദിക്കാൻ ബോൾ ഫലം പ്രവചിക്കുക",
    "earn_per_correct": "ശരിയായ പ്രവചനത്തിന് 5-15 കോയിൻ",
    "ipl_coming": "T20 സീസൺ 2026 മാർച്ച് 26 മുതൽ",
    "get_ready": "ലൈവ് ബോൾ-ബൈ-ബോൾ പ്രവചനങ്ങൾക്ക് തയ്യാറാകൂ!",
    "view_upcoming": "വരാനിരിക്കുന്ന മ്യാച്ചുകൾ കാണുക",
    "watch_live": "ലൈവ് കാണുക", "view_match": "മ്യാച്ച് കാണുക",
    "daily_checkin": "ദൈനംദിന ചെക്ക്-ഇൻ", "check_in_now": "ഇപ്പോൾ ചെക്ക് ഇൻ ചെയ്യുക",
    "checking_in": "ചെക്ക് ഇൻ ആകുന്നു...", "streak_txt": "സ്ട്രീക്ക്:",
    "days": "ദിവസങ്ങൾ", "checked_today": "ഇന്ന് ചെക്ക് ഇൻ ആയി!",
    "come_back_tom": "നാളെ വരൂ", "join_community": "കമ്മ്യൂണിറ്റിയിൽ ചേരൂ",
    "compete_friends": "സുഹൃത്തുക്കളോട് മത്സരിക്കൂ",
    "fantasy_teams": "ഫാന്റസി ടീമുകൾ", "private_leagues": "സ്വകാര്യ ലീഗുകൾ",
    "invite_friends_lbl": "സുഹൃത്തുക്കളെ ക്ഷണിക്കൂ", "mini_games": "മിനി ഗെയിമുകൾ",
    "up_to": "വരെ", "skill_leaderboard": "കഴിവ് ലീഡർബോർഡ്",
    "top_predictors": "കൃത്യതയിൽ മികച്ച പ്രവചകർ",
    "start_predicting": "ചേരാൻ പ്രവചിക്കൂ!",
    "recent_activity": "സമീപകാല പ്രവർത്തനം", "coin_movements": "നിങ്ങളുടെ കോയിൻ ചലനം",
    "no_transactions": "ഇടപാടുകൾ ഇല്ല", "redeem_coins": "കോയിൻ റിഡീം ചെയ്യൂ",
    "starting_10": "10 കോയിൻ മുതൽ", "browse_shop": "ഷോപ്പ് ബ്രൗസ് ചെയ്യൂ",
    "correct_label": "ശരി", "total_label": "ആകെ",
    "beta_label": "നിങ്ങൾ FREE11 ബീറ്റയിലാണ്", "beta_report": "റിപ്പോർട്ട്",
    "balance_label": "ബാലൻസ്", "checkin_failed": "ചെക്ക്-ഇൻ പരാജയപ്പെട്ടു",
    "real_goods": "യഥാർത്ഥ ഉൽപ്പന്നങ്ങൾ", "welcome_back": "FREE11-ലേക്ക് സ്വാഗതം!",
    "quick_start": "പ്രവചിക്കൂ, ഗെയിം കളിക്കൂ, FREE കോയിൻ സമ്പാദിക്കൂ"
}
MISSING["ml"]["profile_page"] = {
    "level": "തലം", "xp": "XP", "progress_next": "അടുത്ത തലത്തിലേക്ക് പുരോഗതി",
    "xp_needed": "XP ആവശ്യം", "max_level": "പരമാവധി തലം", "your_balance": "നിങ്ങളുടെ ബാലൻസ്",
    "redeem_btn": "റിഡീം ചെയ്യുക", "your_stats": "നിങ്ങളുടെ സ്ഥിതിവിവരക്കണക്കുകൾ",
    "predictions": "പ്രവചനങ്ങൾ", "accuracy": "കൃത്യത", "total_earned": "ആകെ സമ്പാദിച്ചത്",
    "invite_friends": "സുഹൃത്തുക്കളെ ക്ഷണിക്കൂ", "earn_badge": "50 സമ്പാദിക്കൂ",
    "my_orders": "എന്റെ ഓർഡറുകൾ", "earn_coins": "കോയിൻ സമ്പാദിക്കൂ",
    "redeem_shop": "ഷോപ്പിൽ റിഡീം ചെയ്യൂ", "help_support": "സഹായവും പിന്തുണയും",
    "sound_effects": "ശബ്ദ ഇഫക്റ്റുകൾ", "settings_title": "ക്രമീകരണങ്ങൾ",
    "admin_dashboard": "അഡ്മിൻ ഡാഷ്ബോർഡ്",
    "legal_info": "നിയമ വിവരങ്ങൾ", "about_free11": "FREE11 നെ കുറിച്ച്",
    "terms_conditions": "നിബന്ധനകളും വ്യവസ്ഥകളും", "privacy_policy": "സ്വകാര്യതാ നയം",
    "community_guidelines": "കമ്മ്യൂണിറ്റി മാർഗ്ഗനിർദ്ദേശങ്ങൾ", "faq": "പതിവ് ചോദ്യങ്ങൾ",
    "log_out": "ലോഗ് ഔട്ട്", "logout_confirm_title": "ഉറപ്പാണോ?",
    "logout_message": "FREE11 അക്കൗണ്ട് ആക്സസ് ചെയ്യാൻ വീണ്ടും സൈൻ ഇൻ ചെയ്യേണ്ടിവരും.",
    "yes_logout": "അതെ, ലോഗ് ഔട്ട്", "version": "FREE11 v1.0",
    "sounds_enabled_msg": "ശബ്ദം പ്രവർത്തനക്ഷമം", "sounds_disabled_msg": "ശബ്ദം പ്രവർത്തനരഹിതം",
    "logged_out_msg": "വിജയകരമായി ലോഗ് ഔട്ട് ആയി",
    "rookie": "പുതുമുഖം", "amateur": "അമേച്വർ", "pro": "പ്രൊ", "expert": "വിദഗ്ധൻ",
    "legend": "ഐതിഹ്യം", "coins_label": "കോയിൻ"
}
MISSING["ml"]["ledger_page"] = {
    "title": "കോയിൻ ലെഡ്ജർ", "available_balance": "ലഭ്യമായ ബാലൻസ്",
    "all": "എല്ലാം", "credits": "ക്രെഡിറ്റ്", "debits": "ഡെബിറ്റ്",
    "no_transactions": "ഇടപാടുകൾ ഇല്ല", "loading": "ലോഡ് ആകുന്നു...",
    "failed": "ലെഡ്ജർ ലോഡ് പരാജയപ്പെട്ടു", "ad_reward": "പരസ്യ പ്രതിഫലം",
    "prediction_reward": "പ്രവചന വിജയം", "referral_reward": "റഫറൽ പ്രതിഫലം",
    "referral_bonus": "റഫറൽ ബോണസ്", "contest_entry": "മത്സര പ്രവേശം",
    "redemption": "റിഡംപ്ഷൻ", "admin_adjust": "അഡ്മിൻ ക്രമീകരണം",
    "signup_bonus": "സൈനപ് ബോണസ്", "daily_checkin": "ദൈനംദിന ചെക്ക്-ഇൻ"
}
MISSING["ml"]["shop_page"] = {
    "title": "ഷോപ്പ്", "subtitle": "Free കോയിൻ യഥാർത്ഥ ഉൽപ്പന്നങ്ങൾക്ക് റിഡീം ചെയ്യുക",
    "all_products": "എല്ലാ ഉൽപ്പന്നങ്ങൾ", "recharge": "റീചാർജ്", "ott": "OTT",
    "food": "ഭക്ഷണം", "vouchers": "വൗച്ചറുകൾ", "electronics": "ഇലക്ട്രോണിക്സ്",
    "fashion": "ഫാഷൻ", "groceries": "പലചരക്ക്", "out_of_stock": "സ്റ്റോക്ക് ഇല്ല",
    "coins_away": "കോയിൻ ആവശ്യം!", "redeem_now": "ഇപ്പോൾ റിഡീം ചെയ്യൂ",
    "level_required": "ലെവൽ", "required": "ആവശ്യം",
    "no_products": "ഉൽപ്പന്നങ്ങൾ കണ്ടെത്തിയില്ല", "try_category": "മറ്റൊരു വിഭാഗം പരീക്ഷിക്കൂ",
    "confirm_redemption": "റിഡംപ്ഷൻ സ്ഥിരീകരിക്കൂ",
    "voucher_delivery": "വൗച്ചർ കോഡ് WhatsApp ഉം ഇമെയിൽ വഴിയും അയക്കും.",
    "mobile_delivery": "മൊബൈൽ നമ്പർ (വൗച്ചർ ഡെലിവറിക്ക്)",
    "your_balance": "നിങ്ങളുടെ ബാലൻസ്", "product_cost": "ഉൽപ്പന്ന വില", "new_balance": "പുതിയ ബാലൻസ്",
    "first_redemption_msg": "ആദ്യ റിഡംപ്ഷൻ! ആസ്വദിക്കൂ!",
    "confirm_btn": "റിഡംപ്ഷൻ സ്ഥിരീകരിക്കൂ", "processing": "പ്രോസസ്സ് ആകുന്നു...",
    "success_title": "അൺലോക്ക്! നിങ്ങളുടെ പ്രതിഫലം തയ്യാർ",
    "success_sub": "കഴിവിലൂടെ സമ്പാദിച്ചു. ആസ്വദിക്കൂ!",
    "delivery_progress": "ഡെലിവറി ആകുന്നു", "continue_shopping": "ഷോപ്പിംഗ് തുടരൂ",
    "valid_mobile": "ഒരു വൈദ്യ മൊബൈൽ നമ്പർ നൽകൂ",
    "brand_funded": "ബ്രാൻഡ് ഫണ്ടഡ്", "limited_drop": "പരിമിതം",
    "stock_label": "സ്റ്റോക്ക്:", "coins_label": "കോയിൻ", "cancel": "റദ്ദാക്കൂ"
}
MISSING["ml"]["footer_links"] = {
    "about": "കുറിച്ച്", "terms": "നിബന്ധനകൾ", "privacy": "സ്വകാര്യത",
    "refund": "തിരിച്ചടവ്", "responsible_play": "ഉത്തരവാദിത്ത കളി",
    "guidelines": "മാർഗ്ഗനിർദ്ദേശങ്ങൾ", "disclaimer": "നിരാകരണം",
    "wallet_info": "വാലറ്റ് വിവരം", "faq": "FAQ", "support": "സഹായം"
}
MISSING["ml"]["legal"] = {"english_only_notice": "ഈ രേഖ നിലവിൽ ഇംഗ്ലീഷിൽ മാത്രം ലഭ്യമാണ്."}
MISSING["ml"]["landing"] = {
    "headline1": "ശരിയായ തീരുമാനങ്ങൾ എടുക്കൂ.", "headline2": "യഥാർത്ഥ പ്രതിഫലം നേടൂ.",
    "subheadline": "FREE11 - നിങ്ങളുടെ ക്രിക്കറ്റ് അറിവ് യഥാർത്ഥ ഉൽപ്പന്നങ്ങളാക്കൂ.",
    "hero_desc": "മ്യാച്ച് നിമിഷങ്ങൾ പ്രവചിക്കൂ, കളിക്കൂ, ദൗത്യങ്ങൾ പൂർത്തിയാക്കൂ.",
    "start_playing": "കളിക്കൂ", "explore_games": "ഗെയിമുകൾ കണ്ടെത്തൂ",
    "start": "ആരംഭിക്കൂ", "login": "ലോഗിൻ", "sign_in": "സൈൻ ഇൻ",
    "platform_title": "FREE11-ൽ എല്ലാം", "platform_subtitle": "ഒരു പ്ലാറ്റ്ഫോം. ആറ് വഴി സമ്പാദിക്കൂ.",
    "feature1_title": "ലൈവ് മ്യാച്ച് പ്രവചനങ്ങൾ", "feature1_desc": "യഥാർത്ഥ സമയത്ത് മ്യാച്ച് നിമിഷം പ്രവചിക്കൂ.",
    "feature2_title": "കഴിവ് അടിസ്ഥാനമാക്കിയ ഗെയിമുകൾ", "feature2_desc": "റമ്മി, പോക്കർ, തീൻ പത്തി കളിക്കൂ.",
    "feature3_title": "ദൗത്യങ്ങൾ & ദൈനംദിന വെല്ലുവിളികൾ", "feature3_desc": "ജോലികൾ പൂർത്തിയാക്കി കോയിൻ നേടൂ.",
    "feature4_title": "ലീഡർബോർഡുകൾ", "feature4_desc": "സുഹൃത്തുക്കളോട് മത്സരിക്കൂ.",
    "feature5_title": "പ്രതിഫല ഷോപ്പ്", "feature5_desc": "കോയിൻ ഉപയോഗിച്ച് വൗച്ചർ റിഡീം ചെയ്യൂ.",
    "feature6_title": "FREE Bucks", "feature6_desc": "പ്രീമിയം മത്സരങ്ങൾ അൺലോക്ക് ചെയ്യൂ.",
    "how_it_works": "ഇത് എങ്ങനെ പ്രവർത്തിക്കുന്നു",
    "step1_title": "അക്കൗണ്ട് ഉണ്ടാക്കൂ", "step1_desc": "60 സെക്കൻഡിൽ സൗജന്യ സൈൻ അപ്പ്",
    "step2_title": "കളിക്കൂ & പ്രവചിക്കൂ", "step2_desc": "മ്യാച്ചുകൾ പ്രവചിക്കൂ, ഗെയിം കളിക്കൂ",
    "step3_title": "കോയിൻ സമ്പാദിക്കൂ", "step3_desc": "ഓരോ ശരിയായ പ്രവചനവും കോയിൻ നൽകുന്നു",
    "step4_title": "ഉൽപ്പന്നങ്ങൾ നേടൂ", "step4_desc": "കോയിൻ ഉപയോഗിച്ച് യഥാർത്ഥ ഉൽപ്പന്നങ്ങൾ",
    "cta_headline": "ഇന്ന് FREE11 യാത്ര ആരംഭിക്കൂ.",
    "cta_desc": "ആയിരക്കണക്കിന് ക്രിക്കറ്റ് ആരാധകരോടൊപ്പം ചേരൂ.",
    "create_account": "അക്കൗണ്ട് ഉണ്ടാക്കൂ", "login_btn": "ലോഗിൻ",
    "disclaimer_title": "നിരാകരണം:", "disclaimer_text": "FREE11 കഴിവ് അടിസ്ഥാനമാക്കിയ പ്ലാറ്റ്ഫോം ആണ്. ജൂദം അല്ല. 18+ മാത്രം.",
    "tagline_coins": "കഴിവ് → കോയിൻ → യഥാർത്ഥ ഉൽപ്പന്നങ്ങൾ",
    "copyright_suffix": "നിങ്ങളുടെ അറിവ്, യഥാർത്ഥ പ്രതിഫലങ്ങൾ"
}
MISSING["ml"]["leaderboard_page"] = {
    "title": "ലീഡർബോർഡുകൾ", "subtitle": "കഴിവിൽ മത്സരിക്കൂ!",
    "loading": "ലോഡ് ആകുന്നു...", "global_tab": "ആഗോള",
    "weekly_tab": "സ്ഥിരം", "streak_tab": "സ്ട്രീക്കുകൾ",
    "global_title": "ആഗോള റാങ്കിംഗ്", "global_desc": "എക്കാലത്തേ കൃത്യത",
    "weekly_title": "ആഴ്ചാ റാങ്കിംഗ്", "weekly_desc": "ഈ ആഴ്ചത്തെ മികച്ച പ്രവചകർ",
    "streak_title": "സ്ട്രീക്ക് കിംഗ്സ്", "streak_desc": "തുടർ ശരിയായ പ്രവചനങ്ങൾ",
    "no_global": "ഇനിയും റാങ്കിംഗ് ഇല്ല.", "no_weekly": "ഈ ആഴ്ച പ്രവചനങ്ങൾ ഇല്ല.", "no_streak": "സ്ട്രീക്കുകൾ ഇല്ല.",
    "duels_title": "പ്രവചന ദ്വന്ദ്വങ്ങൾ", "duels_desc": "സുഹൃത്തുക്കളെ വെല്ലുവിളിക്കൂ!",
    "activity_title": "ആക്ടിവിറ്റി ഫീഡ്",
    "incoming_challenges": "വരുന്ന വെല്ലുവിളികൾ", "active_duels": "സജീവ ദ്വന്ദ്വങ്ങൾ",
    "no_duels": "ദ്വന്ദ്വങ്ങൾ ഇല്ല.", "no_activity": "സമീപകാല പ്രവർത്തനം ഇല്ല",
    "challenged_you": "നിങ്ങളെ വെല്ലുവിളിച്ചു!",
    "accept": "സ്വീകരിക്കൂ", "decline": "നിരസിക്കൂ", "challenge_btn": "ദ്വന്ദ്വത്തിന് വെല്ലുവിളിക്കൂ",
    "won": "ജയിച്ചു", "played": "കളിച്ചു", "win_rate": "ജയ നിരക്ക്",
    "you": "നിങ്ങൾ:", "them": "അവർ:", "accuracy_pct": "കൃത്യത", "correct_label": "ശരി"
}
MISSING["ml"]["referrals_page"] = {
    "title": "റഫർ ചെയ്ത് സമ്പാദിക്കൂ", "your_code": "നിങ്ങളുടെ റഫറൽ കോഡ്",
    "share_msg": "ഈ കോഡ് സുഹൃത്തുക്കളുമായി പങ്കിടൂ. രണ്ടുപേരും കോയിൻ നേടും!",
    "referrals_label": "റഫറലുകൾ", "earned_label": "സമ്പാദിച്ചത്", "per_invite_label": "ക്ഷണ പ്രകാരം",
    "have_code": "റഫറൽ കോഡ് ഉണ്ടോ?", "enter_code": "കോഡ് നൽകൂ",
    "apply": "പ്രയോഗിക്കൂ", "how_it_works": "ഇത് എങ്ങനെ പ്രവർത്തിക്കുന്നു",
    "step1": "നിങ്ങളുടെ അദ്വിതീയ കോഡ് സുഹൃത്തുക്കളുമായി പങ്കിടൂ",
    "step2": "സുഹൃത്ത് സൈൻ അപ്പ് ചെയ്ത് കോഡ് നൽകുന്നു",
    "step3_prefix": "നിങ്ങൾ നേടുന്നു", "step3_suffix": "കോയിൻ, സുഹൃത്ത് 25 കോയിൻ"
}
MISSING["ml"]["cardgames_page"] = {
    "select_game": "ഗെയിം തിരഞ്ഞെടുക്കൂ", "available_rooms": "ലഭ്യമായ മുറികൾ",
    "active_games": "നിങ്ങളുടെ സജീവ ഗെയിമുകൾ", "join_code": "സ്വകാര്യ മുറിയിൽ ചേരൂ",
    "enter_code": "മുറി കോഡ് നൽകൂ", "join": "ചേരൂ", "no_rooms": "മുറികൾ ഇല്ല",
    "create_room": "മുറി ഉണ്ടാക്കൂ", "join_by_code": "കോഡ് ഉപയോഗിച്ച് ചേരൂ",
    "loading": "ലോഡ് ആകുന്നു...", "copy_code": "കോപ്പി", "invite_friend": "സുഹൃത്തിനെ ക്ഷണിക്കൂ",
    "how_it_works": "ഇത് എങ്ങനെ പ്രവർത്തിക്കുന്നു",
    "step1": "ഒരു ഗെയിം തിരഞ്ഞെടുക്കൂ", "step2": "മുറിയിൽ ചേരൂ അല്ലെങ്കിൽ ഉണ്ടാക്കൂ", "step3": "കളിക്കൂ & സമ്പാദിക്കൂ"
}
MISSING["ml"]["support_page"] = {
    "title": "സഹായം & പിന്തുണ", "chat_tab": "ചാറ്റ്", "tickets_tab": "ടിക്കറ്റുകൾ",
    "type_message": "സന്ദേശം ടൈപ്പ് ചെയ്യൂ...", "send": "അയക്കൂ",
    "create_ticket": "ടിക്കറ്റ് ഉണ്ടാക്കൂ", "no_tickets": "ടിക്കറ്റുകൾ ഇല്ല",
    "loading": "ലോഡ് ആകുന്നു..."
}
MISSING["ml"]["notifications"] = {
    "title": "അറിയിപ്പുകൾ", "enable": "അറിയിപ്പുകൾ പ്രവർത്തനക്ഷമമാക്കൂ",
    "settings": "അറിയിപ്പ് ക്രമീകരണങ്ങൾ"
}

# ─── Apply all missing sections ──────────────────────────────────────────────
for lang, sections in MISSING.items():
    data = load(lang)
    for section, content in sections.items():
        if section not in data:
            data[section] = content
            print(f"  Added [{section}] to {lang}")
        else:
            # Merge any missing keys within the section
            for k, v in content.items():
                if k not in data[section]:
                    data[section][k] = v
            print(f"  Merged [{section}] into {lang}")
    save(lang, data)
    print(f"✅ {lang}.json saved")

print("\nAll translation files updated!")
