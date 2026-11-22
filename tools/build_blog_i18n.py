"""English and Russian versions of the blog (tips) on vulkanizacia.ge.

Georgian articles are the originals (hand-written pages, never regenerated here); this script
  - writes /blog/<en-slug>/index.html and /blog/<ru-slug>/index.html for every article (slugs: tools/blog_slugs.json)
  - writes /blog/index-en.html and /blog/index-ru.html (tips index)
  - adds hreflang ka/en/ru to the Georgian pages and points their language switcher, phone menu and footer
    language links at the translations.
Run after build_tyres.py and before build_md.py:  python3 tools/build_blog_i18n.py
"""
import json
import re
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_tyres as T  # noqa: E402  (shared page chrome, schema helpers, URLs)

ROOT, SITE = T.ROOT, T.SITE
SLUGS = T.BLOG_SLUGS
INDEX = {"ka": "/blog/", "en": "/blog/index-en.html", "ru": "/blog/index-ru.html"}
ORDER = ["brakes", "winter", "pressure", "when", "size", "flat", "repair", "rim"]   # newest first; Georgian index gets "brakes" via a marker block
GENERATED_KA = {"brakes"}   # articles whose Georgian version is generated here too (the older ones are hand-written)
DATES = {"brakes": "2026-11-22", "flat": "2026-07-02", "repair": "2026-07-02", "rim": "2026-07-02",
         "winter": "2026-11-03", "pressure": "2026-11-03", "when": "2026-11-03", "size": "2026-11-03"}
IMG = {"brakes": "brakes", "flat": "service", "repair": "service", "rim": "rim-welding", "winter": "cover", "pressure": "service", "when": "van-rear", "size": "cover"}


def url(key, lang):
    return T.blog_url(key, lang)


def L(href, text):
    return f'<a href="{href}" class="text-brand hover:text-amber-400">{text}</a>'


UI = {
    "ka": dict(tips="რჩევები", home="მთავარი", other="სხვა რჩევები", all_tips="ყველა რჩევა →", services="სერვისები", faq="ხშირად დასმული კითხვები",
               help_h="გჭირდებათ დახმარება ახლა?", help_p="მოძრავი ვულკანიზაცია მოვა თქვენთან — 24/7.", more="ვრცლად", read="ვრცლად"),
    "en": dict(tips="Tips", home="Home", other="Other tips", all_tips="All tips →", services="Services", faq="Frequently asked questions",
               help_h="Need help now?", help_p="Our mobile tyre service comes to you — 24/7.", more="Details",
               index_title="Tips on tyres, rims and roadside help — Vulkanizacia.ge",
               index_desc="Useful tips on tyres, rims and roadside help in Tbilisi — what to do if a tyre bursts, repair or replace, winter tyres, tyre pressure, tyre sizes.",
               index_h1="Tips", index_lead="Useful tips on tyres, rims and roadside help — from our experience.", read="Read more"),
    "ru": dict(tips="Советы", home="Главная", other="Другие советы", all_tips="Все советы →", services="Услуги", faq="Частые вопросы",
               help_h="Нужна помощь сейчас?", help_p="Мобильная вулканизация приедет к вам — 24/7.", more="Подробнее",
               index_title="Советы о шинах, дисках и помощи на дороге — Vulkanizacia.ge",
               index_desc="Полезные советы о шинах, дисках и помощи на дороге в Тбилиси — что делать, если лопнула шина, ремонт или замена, зимние шины, давление, размер шины.",
               index_h1="Советы", index_lead="Полезные советы о шинах, дисках и помощи на дороге — из нашего опыта.", read="Читать"),
}
SERVICES = {
    "ka": [("ხუნდების შეცვლა გამოძახებით", T.svc_url("khundebis-shecvla", "ka")), ("საბურავები ზომით", "/saburavebi/"),
           ("მოძრავი ვულკანიზაცია", T.svc_url("modzravi-vulkanizacia", "ka")), ("ბალანსირება", T.svc_url("balansireba", "ka")),
           ("ევაკუატორი", T.svc_url("evakuatori", "ka"))],
    "en": [("Mobile brake repair", T.svc_url("khundebis-shecvla", "en")), ("Tyres by size", "/tyres/"), ("Mobile tyre service", T.svc_url("modzravi-vulkanizacia", "en")),
           ("Seasonal tyre change", T.svc_url("sezonuri-saburavebis-shecvla", "en")), ("Wheel balancing", T.svc_url("balansireba", "en")),
           ("Rim welding", T.svc_url("diskis-dadugheba", "en"))],
    "ru": [("Замена колодок с выездом", T.svc_url("khundebis-shecvla", "ru")), ("Шины по размерам", "/shiny/"), ("Мобильная вулканизация", T.svc_url("modzravi-vulkanizacia", "ru")),
           ("Сезонная замена шин", T.svc_url("sezonuri-saburavebis-shecvla", "ru")), ("Балансировка колёс", T.svc_url("balansireba", "ru")),
           ("Сварка дисков", T.svc_url("diskis-dadugheba", "ru"))],
}


def svc(slug, lang):
    return T.svc_url(slug, lang)


# Article content. Blocks: ("h", text) | ("p", html) | ("ul", [html, ...]) | ("fig", None)
A = {
    "flat": {
        "en": dict(title="Tyre burst on the road — what to do? 6 steps", h1="Tyre burst on the road — what to do?",
                   desc="Tyre burst while driving? 6 safe steps: stay calm, switch on the hazard lights, assess the damage and call a mobile tyre service in Tbilisi 24/7.",
                   keywords="tyre burst what to do, flat tyre on the road, tyre blowout, mobile tyre service Tbilisi",
                   card="A burst tyre is no reason to panic. Here are 6 steps to stay safe.", cta="modzravi-vulkanizacia",
                   blocks=[("p", "A tyre bursting or getting damaged while you drive is a common and dangerous situation. The key is not to panic and to act correctly. Here are 6 steps."),
                           ("h", "1. Stay calm and don't brake hard"),
                           ("p", "Sudden steering or hard braking is dangerous. Hold the wheel firmly, slow down gradually and carefully move the car to the side of the road."),
                           ("h", "2. Switch on the hazard lights"),
                           ("p", "Stop in a safe place, switch on the hazard lights and, if possible, set up the warning triangle — especially at night or on a highway."),
                           ("h", "3. Assess the damage"),
                           ("ul", ["A small puncture in the tread — usually repairable", "Sidewall damage or a large cut — the tyre usually has to be replaced", "A completely burst tyre — do not drive on it"]),
                           ("h", "4. Don't drive on a burst tyre"),
                           ("p", "Driving on a burst or flat tyre damages the rim and is dangerous. It is better to solve the problem on the spot."),
                           ("h", "5. Fit the spare or call a mobile tyre service"),
                           ("p", "If you have a spare wheel and are in a safe place, you can fit it. If not, call a mobile tyre service — we come to you and repair or replace the tyre on the spot."),
                           ("h", "6. Call us — 24/7"),
                           ("p", "Vulkanizacia.ge works 24/7. Call +995 591 90 90 13, tell us your location and a technician usually arrives within 20–30 minutes.")],
                   faq=[("Can I drive a short distance on a burst tyre?", "Not recommended — driving on a burst tyre damages the rim. Stop and call a mobile tyre service."),
                        ("How fast do you arrive?", "Usually within 20–30 minutes in Tbilisi.")]),
        "ru": dict(title="Лопнула шина в дороге — что делать? 6 шагов", h1="Лопнула шина в дороге — что делать?",
                   desc="Лопнула шина в пути? 6 безопасных шагов: сохраняйте спокойствие, включите аварийку, оцените повреждение и вызовите мобильную вулканизацию в Тбилиси 24/7.",
                   keywords="лопнула шина что делать, пробило колесо в дороге, спустило колесо, выездной шиномонтаж Тбилиси",
                   card="Лопнувшая шина — не повод для паники. Вот 6 шагов, которые помогут.", cta="modzravi-vulkanizacia",
                   blocks=[("p", "Повреждение или разрыв шины в дороге — частая и опасная ситуация. Главное — не растеряться и действовать правильно. Вот 6 шагов."),
                           ("h", "1. Сохраняйте спокойствие и не тормозите резко"),
                           ("p", "Резкий поворот руля или внезапное торможение опасны. Крепко держите руль, плавно снижайте скорость и аккуратно уведите машину к обочине."),
                           ("h", "2. Включите аварийную сигнализацию"),
                           ("p", "Остановитесь в безопасном месте, включите аварийку и, если возможно, выставьте знак аварийной остановки — особенно ночью или на трассе."),
                           ("h", "3. Оцените повреждение"),
                           ("ul", ["Небольшой прокол в протекторе — обычно ремонтируется", "Повреждение боковины или большой порез — шину обычно меняют", "Шина полностью лопнула — не ездите на ней"]),
                           ("h", "4. Не ездите на лопнувшей шине"),
                           ("p", "Езда на лопнувшей или спущенной шине повреждает диск и опасна. Лучше решить проблему на месте."),
                           ("h", "5. Поставьте запаску или вызовите вулканизацию"),
                           ("p", "Если есть запасное колесо и вы в безопасном месте, его можно поставить. Если нет — вызовите мобильную вулканизацию: мы приедем и отремонтируем или заменим шину на месте."),
                           ("h", "6. Позвоните нам — 24/7"),
                           ("p", "Vulkanizacia.ge работает 24/7. Позвоните +995 591 90 90 13, сообщите адрес — мастер обычно приезжает в течение 20–30 минут.")],
                   faq=[("Можно немного проехать на лопнувшей шине?", "Не рекомендуется — езда на лопнувшей шине повреждает диск. Лучше остановиться и вызвать мобильную вулканизацию."),
                        ("Как быстро вы приедете?", "По Тбилиси обычно в течение 20–30 минут.")]),
    },
    "repair": {
        "en": dict(title="Tyre repair or replacement — which is better?", h1="Repair or replace a tyre?",
                   desc="When is a tyre repair enough and when should you replace it? Tread, sidewall, puncture location — what we check.",
                   keywords="tyre repair or replace, puncture repair, when to replace a tyre, tyre repair Tbilisi",
                   card="Not every damage means buying a new tyre. Here's how to tell.", cta="modzravi-vulkanizacia",
                   blocks=[("p", "When a tyre is damaged, the question is always the same — repair it or replace it? The right decision depends on the type and location of the damage."),
                           ("h", "When a repair is possible"),
                           ("ul", ["A small puncture (nail, screw) in the tread area", "A puncture up to 6 mm in diameter", "The tyre is otherwise in good condition and not badly worn"]),
                           ("h", "When it is better to replace"),
                           ("ul", ["Sidewall damage or a bulge", "A large cut or several punctures close together", "Worn tread (less than 1.6 mm)", "Old, cracked rubber"]),
                           ("h", "How to know for sure"),
                           ("p", "The best way is to have a technician inspect the tyre. Our mobile tyre service assesses the damage on the spot and tells you honestly whether a repair is enough or a replacement is better.")],
                   faq=[("Is a repaired tyre safe?", "Yes, if the damage is in the tread area and was repaired correctly. Sidewall damage cannot be repaired safely."),
                        ("How long does a repaired tyre last?", "A properly done repair keeps the tyre airtight for the rest of its service life.")]),
        "ru": dict(title="Ремонт или замена шины — что лучше?", h1="Ремонтировать или менять шину?",
                   desc="Когда достаточно ремонта шины, а когда лучше заменить? Протектор, боковина, место прокола — что мы проверяем.",
                   keywords="ремонт или замена шины, ремонт прокола, когда менять шину, ремонт шин Тбилиси",
                   card="Не каждое повреждение означает покупку новой шины. Вот как разобраться.", cta="modzravi-vulkanizacia",
                   blocks=[("p", "При повреждении шины всегда возникает вопрос — ремонтировать или менять? Правильное решение зависит от типа и места повреждения."),
                           ("h", "Когда возможен ремонт"),
                           ("ul", ["Небольшой прокол (гвоздь, саморез) в зоне протектора", "Прокол диаметром до 6 мм", "Шина в остальном исправна и не сильно изношена"]),
                           ("h", "Когда лучше заменить"),
                           ("ul", ["Повреждение боковины или грыжа", "Большой порез или несколько близких проколов", "Изношенный протектор (менее 1,6 мм)", "Старая, потрескавшаяся резина"]),
                           ("h", "Как узнать точно"),
                           ("p", "Лучше всего, если шину осмотрит мастер. Наша мобильная вулканизация оценит повреждение на месте и честно скажет, достаточно ли ремонта или лучше замена.")],
                   faq=[("Безопасна ли отремонтированная шина?", "Да, если повреждение в зоне протектора и ремонт выполнен правильно. Повреждение боковины безопасно отремонтировать нельзя."),
                        ("Сколько прослужит отремонтированная шина?", "Правильно выполненный ремонт сохраняет герметичность на весь оставшийся срок службы шины.")]),
    },
    "rim": {
        "en": dict(title="Rim welding — when is it possible?", h1="Rim welding — when is it possible?",
                   desc="Alloy rim cracked or leaking? When welding restores the rim, when it needs straightening and when it must be replaced.",
                   keywords="rim welding, alloy rim repair, cracked rim, leaking rim, rim welding Tbilisi",
                   card="When welding can save an alloy rim — and when it can't.", cta="diskis-dadugheba",
                   blocks=[("p", "Alloy rims can start leaking or crack over time — after hitting a pothole or because of corrosion. In many cases welding restores the rim without buying a new one."),
                           ("h", "When welding is possible"),
                           ("ul", ["A crack or hole on the inner part of the rim", "A leak caused by corrosion or a small crack", "Aluminium and alloy rims"]),
                           ("h", "When straightening is better"),
                           ("p", "If the rim is bent (not cracked), it usually needs straightening rather than welding. Often both are done together."),
                           ("h", "When it is better to replace"),
                           ("ul", ["A deep structural crack in the centre or on the spokes", "A badly deformed rim", "Damage that affects safety"]),
                           ("h", "What we do"),
                           ("p", "We inspect the rim, clean the damaged area, weld it and check that it is airtight. If needed, we straighten the rim as well — all on call in Tbilisi.")],
                   faq=[("Is a welded rim safe?", "Yes, if the crack is in the inner area and was welded correctly. Structural cracks in the centre are assessed case by case."),
                        ("Will the rim leak after welding?", "A properly done weld stays airtight for a long time; we check the result before returning the wheel.")]),
        "ru": dict(title="Сварка дисков — когда возможна?", h1="Сварка дисков — когда возможна?",
                   desc="Литой диск треснул или травит воздух? Когда сварка восстанавливает диск, когда нужна правка, а когда — замена.",
                   keywords="сварка дисков, ремонт литых дисков, трещина на диске, диск травит воздух, сварка дисков Тбилиси",
                   card="Когда сварка спасёт литой диск — а когда нет.", cta="diskis-dadugheba",
                   blocks=[("p", "Литые диски со временем могут начать травить воздух или треснуть — после ямы или из-за коррозии. Во многих случаях сварка восстанавливает диск без покупки нового."),
                           ("h", "Когда возможна сварка"),
                           ("ul", ["Трещина или отверстие на внутренней части диска", "Утечка воздуха из-за коррозии или небольшой трещины", "Алюминиевые и литые диски"]),
                           ("h", "Когда лучше правка"),
                           ("p", "Если диск погнут (а не треснул), обычно нужна правка, а не сварка. Часто обе процедуры выполняются вместе."),
                           ("h", "Когда лучше заменить"),
                           ("ul", ["Глубокая структурная трещина в центре или на спицах", "Сильно деформированный диск", "Повреждение, влияющее на безопасность"]),
                           ("h", "Что мы делаем"),
                           ("p", "Осматриваем диск, зачищаем повреждённое место, свариваем и проверяем герметичность. При необходимости правим диск — всё с выездом по Тбилиси.")],
                   faq=[("Безопасен ли сваренный диск?", "Да, если трещина во внутренней зоне и сварка выполнена правильно. Структурные трещины в центре оцениваем индивидуально."),
                        ("Будет ли диск травить после сварки?", "Правильно выполненная сварка надолго сохраняет герметичность; мы проверяем результат перед установкой колеса.")]),
    },
    "winter": {
        "en": dict(title="Winter tyres — when to change?", h1="Winter tyres — when to change?",
                   desc="When to fit winter tyres in Tbilisi? The 7°C rule, how winter tyres differ from summer tyres and how to prepare for mountain roads.",
                   keywords="winter tyres when to change, when to fit winter tyres, 7 degree rule, winter tyres Tbilisi",
                   card="The 7°C rule, how winter tyres differ and tips for mountain roads.", cta="sezonuri-saburavebis-shecvla",
                   blocks=[("p", "Winter tyres are not only for snow. In cold weather the rubber of a summer tyre hardens and grip gets worse — even on dry asphalt."),
                           ("h", "The 7°C rule"),
                           ("p", "When the average daily temperature stays below about 7°C, a winter tyre grips the road better than a summer one. In Tbilisi this usually happens from mid-November, and the switch back to summer tyres in late March or April, when the temperature stays above 7°C."),
                           ("h", "How winter tyres differ"),
                           ("ul", ["Softer rubber that stays flexible in the cold", "Deeper tread and many fine sipes for grip on snow and ice",
                                   "Better braking on wet and cold roads", "M+S marking or the mountain-snowflake symbol (3PMSF)"]),
                           ("h", "Mountain roads and winter trips"),
                           ("p", "If you are heading to Gudauri, Bakuriani or other mountain areas in winter, fit winter tyres in advance and carry snow chains — during snowfall, mountain passes may be open only to cars with winter tyres or chains."),
                           ("h", "What to check on winter tyres"),
                           ("ul", ["Tread depth — at least 4 mm is recommended for winter tyres", "Age — rubber older than 6 years hardens even if the tread is deep",
                                   "Cracks and bulges on the sidewall", "Pressure — it drops in the cold, so check it more often"]),
                           ("h", "Winter tyre fitting on site"),
                           ("p", "No need to queue: {seasonal} — we come to your home or office, mount the tyres on your rims, balance them and check the pressure. Need tyres? See {wtyres}.")],
                   faq=[("Can I fit only two winter tyres?", "Not recommended — winter tyres should be on all four wheels so the car stays stable when braking and cornering."),
                        ("Will all-season tyres cope with winter?", "For Tbilisi's mild winter, good all-season tyres are often enough, but on snow, ice and mountain roads winter tyres are much better."),
                        ("How long do winter tyres last?", "Usually 4–5 seasons, depending on mileage and storage. After 6 years the rubber hardens and they are best replaced.")]),
        "ru": dict(title="Зимние шины — когда менять?", h1="Зимние шины — когда менять?",
                   desc="Когда ставить зимние шины в Тбилиси? Правило 7°C, чем зимние шины отличаются от летних и как подготовиться к горным дорогам.",
                   keywords="когда менять на зимнюю резину, когда ставить зимние шины, правило 7 градусов, зимние шины Тбилиси",
                   card="Правило 7°C, отличия зимних шин и советы для горных дорог.", cta="sezonuri-saburavebis-shecvla",
                   blocks=[("p", "Зимние шины нужны не только для снега. В холод резина летней шины твердеет, и сцепление ухудшается — даже на сухом асфальте."),
                           ("h", "Правило 7°C"),
                           ("p", "Когда среднесуточная температура стабильно опускается ниже примерно 7°C, зимняя шина держит дорогу лучше летней. В Тбилиси это обычно с середины ноября, а вернуться на летние шины стоит в конце марта или в апреле, когда температура стабильно выше 7°C."),
                           ("h", "Чем отличаются зимние шины"),
                           ("ul", ["Мягкая резина, которая сохраняет эластичность на холоде", "Глубокий протектор и много ламелей для сцепления на снегу и льду",
                                   "Лучшее торможение на мокрой и холодной дороге", "Маркировка M+S или символ горы со снежинкой (3PMSF)"]),
                           ("h", "Горные дороги и зимние поездки"),
                           ("p", "Если зимой едете в Гудаури, Бакуриани или другие горные районы, заранее поставьте зимние шины и возьмите цепи — во время снегопада проезд через перевалы может быть разрешён только на зимних шинах или с цепями."),
                           ("h", "Что проверить на зимних шинах"),
                           ("ul", ["Глубина протектора — для зимних шин желательно не менее 4 мм", "Возраст — резина старше 6 лет твердеет, даже если протектор глубокий",
                                   "Трещины и грыжи на боковине", "Давление — на холоде оно падает, поэтому проверяйте чаще"]),
                           ("h", "Установка зимних шин на месте"),
                           ("p", "Без очередей: {seasonal} — приедем к дому или офису, смонтируем шины на диски, отбалансируем и проверим давление. Нужны шины? Смотрите {wtyres}.")],
                   faq=[("Можно поставить только две зимние шины?", "Не рекомендуется — зимние шины должны стоять на всех четырёх колёсах, чтобы машина оставалась устойчивой при торможении и в поворотах."),
                        ("Справятся ли всесезонные шины с зимой?", "Для мягкой тбилисской зимы хорошие всесезонные шины часто подходят, но на снегу, льду и горных дорогах зимние шины гораздо лучше."),
                        ("Сколько служат зимние шины?", "Обычно 4–5 сезонов, в зависимости от пробега и хранения. Через 6 лет резина твердеет, и шины лучше заменить.")]),
    },
    "pressure": {
        "en": dict(title="Tyre pressure — what should it be?", h1="Tyre pressure — what should it be?",
                   desc="What should your tyre pressure be? Where to find the manufacturer's value, how to check it correctly and what happens with low or high pressure.",
                   keywords="tyre pressure, correct tyre pressure, how to check tyre pressure, tyre losing pressure",
                   card="Where to find the right pressure, how to check it and why tyres lose air.", cta="modzravi-vulkanizacia",
                   blocks=[("p", "The right pressure makes tyres last longer, saves fuel and improves braking. It is also the check people forget most often."),
                           ("h", "Where to find the right pressure"),
                           ("p", "The recommended pressure is on the sticker in the driver's door frame, inside the fuel filler flap or in the car manual. For most passenger cars it is about 2.0–2.5 bar (29–36 PSI), but always follow your car's own values — front and rear wheels, and a fully loaded car, often have different values."),
                           ("h", "How to check it correctly"),
                           ("ul", ["Check cold tyres — before driving or after the car has stood for a few hours", "Check once a month and before long trips",
                                   "Don't forget the spare wheel", "Pressure drops in the cold — check more often in winter"]),
                           ("h", "Dangers of low pressure"),
                           ("ul", ["The tyre wears quickly on the edges", "Fuel consumption goes up", "Handling and braking get worse", "Higher risk of overheating and tyre damage"]),
                           ("h", "Dangers of high pressure"),
                           ("ul", ["The tyre wears in the centre", "Less grip, especially on wet roads", "A harsher ride"]),
                           ("h", "Losing pressure often?"),
                           ("p", "If one tyre keeps losing air, it is probably a puncture, a damaged rim edge or a valve problem. Our {mobile} finds the cause on the spot and repairs it; for a cracked rim — {rimweld}.")],
                   faq=[("What should my car's tyre pressure be?", "For most passenger cars 2.0–2.5 bar (29–36 PSI). The exact value is on the driver's door frame or the fuel filler flap."),
                        ("Should I add pressure in winter?", "Pressure drops in the cold, so check it more often in winter and top it up to the manufacturer's recommended value."),
                        ("Why does my tyre lose pressure?", "Most often because of a puncture, a damaged rim edge, a leaking valve or natural loss over time.")]),
        "ru": dict(title="Давление в шинах — каким оно должно быть?", h1="Давление в шинах — каким оно должно быть?",
                   desc="Каким должно быть давление в шинах? Где найти значение производителя, как правильно проверить и что бывает при низком или высоком давлении.",
                   keywords="давление в шинах, какое давление в шинах, как проверить давление, шина теряет давление",
                   card="Где найти правильное давление, как его проверить и почему шина теряет воздух.", cta="modzravi-vulkanizacia",
                   blocks=[("p", "Правильное давление продлевает срок службы шин, экономит топливо и улучшает торможение. И это самая часто забываемая проверка."),
                           ("h", "Где найти правильное давление"),
                           ("p", "Рекомендуемое давление указано на наклейке в проёме водительской двери, на внутренней стороне лючка бензобака или в руководстве автомобиля. Для большинства легковых машин это около 2,0–2,5 бар (29–36 PSI), но всегда ориентируйтесь на данные своей модели — для передних и задних колёс, а также при полной загрузке значения часто разные."),
                           ("h", "Как правильно проверить"),
                           ("ul", ["Проверяйте холодные шины — до поездки или после нескольких часов стоянки", "Проверяйте раз в месяц и перед дальней поездкой",
                                   "Не забывайте про запасное колесо", "На холоде давление падает — зимой проверяйте чаще"]),
                           ("h", "Чем опасно низкое давление"),
                           ("ul", ["Шина быстро изнашивается по краям", "Растёт расход топлива", "Ухудшаются управляемость и торможение", "Растёт риск перегрева и повреждения шины"]),
                           ("h", "Чем опасно высокое давление"),
                           ("ul", ["Шина изнашивается по центру", "Хуже сцепление, особенно на мокрой дороге", "Жёстче ход"]),
                           ("h", "Давление часто падает?"),
                           ("p", "Если одна шина постоянно теряет воздух, вероятно, это прокол, повреждённая кромка диска или проблема с вентилем. {mobile} найдёт причину на месте и устранит её, а при трещине диска поможет {rimweld}.")],
                   faq=[("Каким должно быть давление в шинах автомобиля?", "Для большинства легковых машин 2,0–2,5 бар (29–36 PSI). Точное значение указано в проёме водительской двери или на лючке бензобака."),
                        ("Нужно ли зимой подкачивать шины?", "На холоде давление падает, поэтому зимой проверяйте его чаще и доводите до значения, рекомендованного производителем."),
                        ("Почему шина теряет давление?", "Чаще всего из-за прокола, повреждённой кромки диска, негерметичного вентиля или естественной потери со временем.")]),
    },
    "when": {
        "en": dict(title="When should a tyre be replaced? Wear and age", h1="When should a tyre be replaced? Wear and age",
                   desc="When to replace a tyre: tread depth, wear indicators, tyre age (DOT code), cracks and bulges.",
                   keywords="when to replace tyres, tyre tread depth, tyre age, DOT code, worn tyres",
                   card="Tread depth, the DOT code and signs a tyre needs replacing.", cta="modzravi-vulkanizacia",
                   blocks=[("p", "Old or worn tyres are one of the most common reasons a car slides on wet roads and the braking distance grows. Here is what to check."),
                           ("h", "Tread depth"),
                           ("p", "In many countries the legal minimum is 1.6 mm, but for safety it is better to replace summer tyres at 3 mm and winter tyres at 4 mm. The tread grooves have wear indicators — small raised bars. When the tread is worn down to them, the tyre must be replaced."),
                           ("h", "Tyre age — the DOT code"),
                           ("p", "The four-digit code on the sidewall shows the week and year of manufacture: for example, 2321 means week 23 of 2021. Rubber ages over time, so inspect tyres older than 6 years carefully and replace tyres older than 10 years even if the tread is still deep."),
                           ("h", "Signs a tyre needs replacing"),
                           ("ul", ["Cracks on the sidewall or tread", "A bulge on the sidewall — driving on it is dangerous", "Uneven wear — may point to a pressure or suspension problem",
                                   "Vibration that stays even after balancing", "Frequent punctures on a heavily worn tyre"]),
                           ("h", "How to make tyres last longer"),
                           ("ul", ["Check the pressure once a month — {pressure}", "Balance the wheels every time you change tyres — {balancing}",
                                   "Avoid kerbs and potholes at speed", "Store seasonal tyres in a dry, cool place, away from sunlight"]),
                           ("p", "Need new tyres? {tyres} — we bring them and fit them on site: {seasonal}.")],
                   faq=[("How many years does a tyre last?", "Usually 4–6 years, depending on mileage and care. After 6 years inspect the tyre every year, and after 10 years replace it."),
                        ("Can I replace just one tyre?", "It is better to replace tyres in pairs — both on the same axle — so the car handles predictably."),
                        ("Should new tyres go on the front or the rear?", "Most manufacturers recommend fitting new tyres on the rear axle — it reduces the risk of skidding on wet roads.")]),
        "ru": dict(title="Когда менять шины? Износ и возраст", h1="Когда менять шины? Износ и возраст",
                   desc="Когда менять шину: глубина протектора, индикатор износа, возраст шины (код DOT), трещины и грыжи.",
                   keywords="когда менять шины, глубина протектора, возраст шины, код DOT, износ шин",
                   card="Глубина протектора, код DOT и признаки, что шину пора менять.", cta="modzravi-vulkanizacia",
                   blocks=[("p", "Старые или изношенные шины — одна из самых частых причин, по которым машину заносит на мокрой дороге, а тормозной путь растёт. Вот что нужно проверить."),
                           ("h", "Глубина протектора"),
                           ("p", "Во многих странах допустимый минимум — 1,6 мм, но для безопасности летние шины лучше менять при 3 мм, а зимние — при 4 мм. В канавках протектора есть индикаторы износа — небольшие выступы. Если протектор стёрся до них, шину нужно менять."),
                           ("h", "Возраст шины — код DOT"),
                           ("p", "Четырёхзначный код на боковине показывает неделю и год выпуска: например, 2321 означает 23-ю неделю 2021 года. Резина со временем стареет, поэтому шины старше 6 лет внимательно осматривайте, а старше 10 лет — меняйте, даже если протектор ещё глубокий."),
                           ("h", "Признаки, что шину пора менять"),
                           ("ul", ["Трещины на боковине или протекторе", "Грыжа на боковине — ездить с ней опасно", "Неравномерный износ — может указывать на проблему с давлением или подвеской",
                                   "Вибрация, которая не проходит после балансировки", "Частые проколы на сильно изношенной шине"]),
                           ("h", "Как продлить срок службы шин"),
                           ("ul", ["Проверяйте давление раз в месяц — {pressure}", "Балансируйте колёса при каждой замене шин — {balancing}",
                                   "Избегайте бордюров и ям на скорости", "Храните сезонные шины в сухом прохладном месте, вдали от солнца"]),
                           ("p", "Нужны новые шины? {tyres} — привезём и установим на месте: {seasonal}.")],
                   faq=[("Сколько лет служит шина?", "Обычно 4–6 лет, в зависимости от пробега и ухода. После 6 лет осматривайте шину ежегодно, а после 10 лет — меняйте."),
                        ("Можно заменить только одну шину?", "Лучше менять шины парами — обе на одной оси, — чтобы машина вела себя предсказуемо."),
                        ("Новые шины ставить вперёд или назад?", "Большинство производителей рекомендуют ставить новые шины на заднюю ось — это снижает риск заноса на мокрой дороге.")]),
    },
    "size": {
        "en": dict(title="Tyre size — how to read 205/55 R16?", h1="Tyre size — how to read 205/55 R16?",
                   desc="How to read a tyre size and markings: 205/55 R16 91V — width, profile, rim diameter, load and speed index.",
                   keywords="how to read tyre size, tyre size explained, 205/55 R16 meaning, tyre markings, load index",
                   card="205/55 R16 91V — what every number and letter means.", cta="sezonuri-saburavebis-shecvla",
                   fig=("tyre-size-205-55-r16-en", "How to read a tyre size: 205/55 R16 91V — width 205 mm, profile 55%, R radial construction, 16-inch rim, load index 91 (up to 615 kg), speed index V (up to 240 km/h)",
                        "Tyre markings explained on 205/55 R16 91V — what every number and letter means."),
                   blocks=[("p", "The numbers and letters on the tyre sidewall tell you everything you need to choose a new tyre. Let's go through an example: 205/55 R16 91V."),
                           ("fig", None),
                           ("h", "Decoding the markings"),
                           ("ul", ["<strong>205</strong> — tyre width in millimetres", "<strong>55</strong> — profile height as a percentage of the width (55% of 205 mm)",
                                   "<strong>R</strong> — radial construction (almost all modern tyres)", "<strong>16</strong> — rim diameter in inches",
                                   "<strong>91</strong> — load index (91 = up to 615 kg per tyre)", "<strong>V</strong> — speed index (V = up to 240 km/h)"]),
                           ("h", "Where to find your car's tyre size"),
                           ("p", "Approved sizes are listed in the car manual and often on the sticker in the driver's door frame. The simplest way is to read the size printed on your current tyre."),
                           ("h", "Other important markings"),
                           ("ul", ["<strong>DOT</strong> and a four-digit code — week and year of manufacture", "<strong>M+S</strong> or the mountain-snowflake symbol — winter or all-season tyre",
                                   "<strong>XL</strong> (Extra Load) — reinforced tyre for higher loads", "<strong>Run Flat</strong> (RSC, ROF, ZP) — can be driven a limited distance after a puncture",
                                   "<strong>TWI</strong> — location of the wear indicator"]),
                           ("h", "Can I fit a different size?"),
                           ("p", "The rim diameter must match, and the width and profile must be among the options approved by the car manufacturer. The load and speed index must not be lower than the original. If in doubt, call us — we will help you choose."),
                           ("p", "Find tyres in your size: {tyres}. Fitting and balancing on site: {seasonal}.")],
                   faq=[("What does R16 mean?", "R stands for radial construction and 16 for the rim diameter in inches — the tyre fits a 16-inch rim."),
                        ("How do I find a tyre's production date?", "On the sidewall, after the DOT marking, find the four-digit code: the first two digits are the week, the last two the year. For example, 0823 means week 8 of 2023."),
                        ("Can I have different tyre sizes front and rear?", "Only if the car manufacturer specifies it (on some sports models). Otherwise all four tyres should be the same size.")]),
        "ru": dict(title="Размер шины — как прочитать 205/55 R16?", h1="Размер шины — как прочитать 205/55 R16?",
                   desc="Как прочитать размер и маркировку шины: 205/55 R16 91V — ширина, профиль, диаметр диска, индекс нагрузки и скорости.",
                   keywords="как прочитать размер шины, расшифровка размера шин, 205/55 R16 что означает, маркировка шин, индекс нагрузки",
                   card="205/55 R16 91V — что означает каждая цифра и буква.", cta="sezonuri-saburavebis-shecvla",
                   fig=("tyre-size-205-55-r16-ru", "Как прочитать размер шины: 205/55 R16 91V — ширина 205 мм, профиль 55%, R — радиальная конструкция, диск 16 дюймов, индекс нагрузки 91 (до 615 кг), индекс скорости V (до 240 км/ч)",
                        "Маркировка шины на примере 205/55 R16 91V — что означает каждая цифра и буква."),
                   blocks=[("p", "Цифры и буквы на боковине шины говорят всё, что нужно для выбора новой шины. Разберём на примере: 205/55 R16 91V."),
                           ("fig", None),
                           ("h", "Расшифровка маркировки"),
                           ("ul", ["<strong>205</strong> — ширина шины в миллиметрах", "<strong>55</strong> — высота профиля в процентах от ширины (55% от 205 мм)",
                                   "<strong>R</strong> — радиальная конструкция (почти все современные шины)", "<strong>16</strong> — диаметр диска в дюймах",
                                   "<strong>91</strong> — индекс нагрузки (91 = до 615 кг на шину)", "<strong>V</strong> — индекс скорости (V = до 240 км/ч)"]),
                           ("h", "Где найти размер шин своего автомобиля"),
                           ("p", "Допустимые размеры указаны в руководстве автомобиля и часто на наклейке в проёме водительской двери. Проще всего — прочитать размер на нынешней шине."),
                           ("h", "Другие важные обозначения"),
                           ("ul", ["<strong>DOT</strong> и четырёхзначный код — неделя и год выпуска", "<strong>M+S</strong> или символ горы со снежинкой — зимняя или всесезонная шина",
                                   "<strong>XL</strong> (Extra Load) — усиленная шина для большей нагрузки", "<strong>Run Flat</strong> (RSC, ROF, ZP) — после прокола на шине можно проехать ограниченное расстояние",
                                   "<strong>TWI</strong> — место индикатора износа"]),
                           ("h", "Можно ли поставить другой размер?"),
                           ("p", "Диаметр диска должен совпадать, а ширина и профиль — входить в допустимые производителем варианты. Индексы нагрузки и скорости не должны быть ниже заводских. Если сомневаетесь — позвоните, поможем с подбором."),
                           ("p", "Шины вашего размера: {tyres}. Монтаж и балансировка на месте: {seasonal}.")],
                   faq=[("Что означает R16?", "R — радиальная конструкция, 16 — диаметр диска в дюймах, то есть шина подходит к 16-дюймовому диску."),
                        ("Как узнать дату выпуска шины?", "На боковине после обозначения DOT найдите четырёхзначный код: первые две цифры — неделя, последние две — год. Например, 0823 — 8-я неделя 2023 года."),
                        ("Можно ли ставить спереди и сзади шины разного размера?", "Только если это предусмотрено производителем автомобиля (на некоторых спортивных моделях). В остальных случаях все четыре шины должны быть одного размера.")]),
    },
}

A["brakes"] = {
    "ka": dict(title="ხუნდები: რა არის და როდის უნდა შეიცვალოს — 6 ნიშანი", h1="როდის უნდა შეიცვალოს ხუნდები — 6 ნიშანი",
               desc="რა არის სამუხრუჭე ხუნდები და როდის უნდა შეიცვალოს: 6 ნიშანი — ჭრიალი, ნიშანი დაფაზე, ვიბრაცია და სხვა. რამდენ ხანში ერთხელ იცვლება წინა და უკანა ხუნდები.",
               keywords="ხუნდები, ხუნდები რა არის, როდის უნდა შეიცვალოს ხუნდები, სამუხრუჭე ხუნდები, ხუნდების ცვეთა, წინა ხუნდები, უკანა ხუნდები, ხუნდების შეცვლა",
               card="ჭრიალი, ნიშანი დაფაზე, ვიბრაცია — როდის არის დრო ხუნდების შესაცვლელად.", cta="khundebis-shecvla",
               fig=("brake-pad-wear", "როდის უნდა შეიცვალოს ხუნდები: ახალ ხუნდს ხახუნის ფენა დაახლოებით 10–12 მმ აქვს, 3 მმ-ზე ნაკლები კი უკვე შესაცვლელია",
                    "ახალი და გაცვეთილი ხუნდი — როცა ხახუნის ფენა 3 მმ-მდე გაცვდება, ხუნდი უნდა შეიცვალოს."),
               blocks=[("p", "სამუხრუჭე ხუნდები მანქანის უსაფრთხოების ერთ-ერთი მთავარი ნაწილია. თუ დროულად არ შეიცვალა, იზრდება დამუხრუჭების მანძილი და ზიანდება სამუხრუჭე დისკებიც. ქვემოთ — რა არის ხუნდები და 6 ნიშანი, რომ მათი შეცვლის დროა."),
                       ("h", "რა არის ხუნდები"),
                       ("p", "ხუნდი არის ლითონის ფირფიტა ხახუნის ფენით. დამუხრუჭებისას სუპორტი ხუნდებს სამუხრუჭე დისკზე აჭერს და ხახუნი მანქანას აჩერებს. ყოველ დამუხრუჭებაზე ხახუნის ფენა ოდნავ ცვდება."),
                       ("fig", None),
                       ("h", "6 ნიშანი, რომ ხუნდები შესაცვლელია"),
                       ("ul", ["<strong>ჭრიალი დამუხრუჭებისას</strong> — ბევრ ხუნდს აქვს ლითონის ინდიკატორი, რომელიც გაცვეთისას ჭრიალს იწვევს",
                               "<strong>ღრჭიალი</strong> — ხახუნის ფენა თითქმის აღარ არის და ლითონი დისკს ეხება; შეცვალეთ დაუყოვნებლივ",
                               "<strong>ნიშანი დაფაზე</strong> — ცვეთის სენსორის მქონე მანქანებზე",
                               "<strong>დამუხრუჭების მანძილი გაიზარდა</strong> ან პედალს მეტი ძალით აჭერთ",
                               "<strong>ვიბრაცია</strong> პედალზე ან საჭეზე დამუხრუჭებისას — ხშირად დისკის პრობლემაა",
                               "<strong>მანქანა ერთ მხარეს იწევს</strong> დამუხრუჭებისას"]),
                       ("h", "რამდენ ხანში ერთხელ იცვლება ხუნდები"),
                       ("p", "ზუსტი გარბენი არ არსებობს — ეს დამოკიდებულია მართვის სტილზე, გზებსა და ხუნდების ხარისხზე. ქალაქში, ხშირი დამუხრუჭებით, ხუნდები უფრო სწრაფად ცვდება. სასურველია, ხუნდები დაახლოებით ყოველ 10 000 კმ-ში შემოწმდეს. ახალ ხუნდს ხახუნის ფენა დაახლოებით 10–12 მმ აქვს; როცა 3 მმ-მდე გაცვდება, შეცვლის დროა."),
                       ("h", "წინა თუ უკანა ხუნდები"),
                       ("p", "წინა ხუნდები, როგორც წესი, უფრო სწრაფად ცვდება, რადგან დამუხრუჭებისას დატვირთვის დიდი ნაწილი წინა ღერძზე მოდის. ხუნდები ყოველთვის წყვილად იცვლება — ერთი ღერძის ორივე ბორბალზე. დისკი იცვლება, თუ ძალიან გაცვეთილია, ღრმად არის დაკაწრული ან ვიბრაციას იწვევს."),
                       ("h", "როდის არ შეიძლება მოძრაობის გაგრძელება"),
                       ("p", "თუ პედალი იატაკამდე ჩადის, სამუხრუჭე სითხე ჟონავს ან დაფაზე მუხრუჭის წითელი ნიშანი ანთია, გაჩერდით და ნუ გააგრძელებთ მოძრაობას. საჭიროების შემთხვევაში გამოიძახეთ {tow}."),
                       ("p", "ხუნდების შეცვლა ადგილზე — {brakes}: მოვალთ თქვენთან, მოგიტანთ ხუნდებს ან დაგიყენებთ თქვენსას.")],
               faq=[("რა არის ხუნდები?", "ლითონის ფირფიტა ხახუნის ფენით, რომელსაც დამუხრუჭებისას სუპორტი სამუხრუჭე დისკზე აჭერს და მანქანას აჩერებს."),
                    ("რამდენ კილომეტრში იცვლება ხუნდები?", "ზუსტი გარბენი არ არსებობს — დამოკიდებულია მართვის სტილსა და გზებზე. შეამოწმეთ დაახლოებით ყოველ 10 000 კმ-ში და შეცვალეთ, როცა ხახუნის ფენა 3 მმ-მდე გაცვდება."),
                    ("რატომ ჭრიალებს ხუნდები?", "ხშირად ცვეთის ინდიკატორი გაძლევთ სიგნალს, რომ ხუნდები გაცვდა. ჭრიალი შეიძლება ახალ ან დაბინძურებულ ხუნდებსაც ახასიათებდეს — სჯობს, შემოწმდეს.")]),
    "en": dict(title="Brake pads: when to replace them — 6 symptoms and how often", h1="When to replace brake pads — 6 signs",
               desc="What brake pads are and when to replace them: 6 symptoms — squeaking, the wear light, vibration and more. How often front and rear brake pads need replacing.",
               keywords="when to replace brake pads, brake pads problems symptoms, brake pad wear indicator, how often replace brake pads, front or rear brake pads",
               card="Squeaking, a warning light, vibration — when it's time for new brake pads.", cta="khundebis-shecvla",
               fig=("brake-pad-wear-en", "When to replace brake pads: a new pad has about 10–12 mm of friction material, under 3 mm it needs replacing",
                    "New vs worn brake pad — replace the pad when the friction material is down to about 3 mm."),
               blocks=[("p", "Brake pads are one of the most important safety parts of a car. If they are not replaced in time, the braking distance gets longer and the brake discs get damaged too. Here is what brake pads are and 6 signs it's time to replace them."),
                       ("h", "What are brake pads"),
                       ("p", "A brake pad is a metal backing plate with a layer of friction material. When you brake, the caliper presses the pads against the brake disc and the friction stops the car. Every time you brake, the friction material wears down a little."),
                       ("fig", None),
                       ("h", "6 signs your brake pads need replacing"),
                       ("ul", ["<strong>Squeaking when braking</strong> — many pads have a metal wear indicator that squeals when the pad is worn",
                               "<strong>Grinding</strong> — the friction material is almost gone and metal touches the disc; replace immediately",
                               "<strong>Warning light on the dashboard</strong> — on cars with a pad wear sensor",
                               "<strong>Longer braking distance</strong>, or you have to press the pedal harder",
                               "<strong>Vibration</strong> in the pedal or steering wheel when braking — often a disc problem",
                               "<strong>The car pulls to one side</strong> when braking"]),
                       ("h", "How often should brake pads be replaced"),
                       ("p", "There is no exact mileage — it depends on driving style, roads and pad quality. In city traffic with frequent braking, pads wear faster. It is a good idea to check the pads roughly every 10,000 km. A new pad has about 10–12 mm of friction material; when it is down to about 3 mm, it's time to replace it."),
                       ("h", "Front or rear brake pads"),
                       ("p", "Front pads usually wear faster, because most of the braking load goes to the front axle. Pads are always replaced in pairs — on both wheels of the same axle. A disc is replaced if it is badly worn, deeply scored or causes vibration."),
                       ("h", "When you should not keep driving"),
                       ("p", "If the pedal sinks to the floor, brake fluid is leaking or the red brake warning light is on, stop and don't continue driving. If needed, call a {tow}."),
                       ("p", "Brake pad replacement on site — {brakes}: we come to you and bring the pads, or fit yours.")],
               faq=[("What are brake pads?", "A metal plate with a friction layer that the caliper presses against the brake disc to stop the car."),
                    ("How many kilometres do brake pads last?", "There is no exact figure — it depends on driving style and roads. Check them roughly every 10,000 km and replace them when the friction material is down to about 3 mm."),
                    ("Why do my brakes squeak?", "Often the wear indicator is telling you the pads are worn. New or dirty pads can also squeak — it's best to have them checked.")]),
    "ru": dict(title="Тормозные колодки: когда менять — 6 признаков износа", h1="Когда менять тормозные колодки — 6 признаков",
               desc="Что такое тормозные колодки и когда их менять: 6 признаков износа — скрип, индикатор на панели, вибрация и другие. Как часто меняют передние и задние колодки.",
               keywords="когда менять тормозные колодки, признаки износа тормозных колодок, колодки скрипят, колодки трутся о диск что делать, передние или задние колодки",
               card="Скрип, индикатор на панели, вибрация — когда пора менять колодки.", cta="khundebis-shecvla",
               fig=("brake-pad-wear-ru", "Когда менять тормозные колодки: у новой колодки фрикционный слой около 10–12 мм, меньше 3 мм — пора менять",
                    "Новая и изношенная колодка — когда фрикционный слой стёрся до 3 мм, колодку нужно менять."),
               blocks=[("p", "Тормозные колодки — одна из главных деталей безопасности автомобиля. Если вовремя их не заменить, увеличивается тормозной путь и страдают тормозные диски. Разберём, что такое колодки, и 6 признаков, что их пора менять."),
                       ("h", "Что такое тормозные колодки"),
                       ("p", "Колодка — это металлическая основа с фрикционным слоем. При торможении суппорт прижимает колодки к тормозному диску, и трение останавливает машину. С каждым торможением фрикционный слой немного стирается."),
                       ("fig", None),
                       ("h", "6 признаков, что колодки пора менять"),
                       ("ul", ["<strong>Скрип при торможении</strong> — у многих колодок есть металлический индикатор износа, который начинает скрипеть",
                               "<strong>Скрежет, колодки трутся о диск</strong> — фрикционный слой почти стёрся и металл касается диска; меняйте немедленно",
                               "<strong>Индикатор на панели</strong> — на машинах с датчиком износа колодок",
                               "<strong>Тормозной путь стал длиннее</strong> или педаль приходится нажимать сильнее",
                               "<strong>Вибрация</strong> педали или руля при торможении — часто это проблема диска",
                               "<strong>Машину уводит в сторону</strong> при торможении"]),
                       ("h", "Как часто менять тормозные колодки"),
                       ("p", "Точного пробега нет — всё зависит от стиля вождения, дорог и качества колодок. В городе, где тормозить приходится часто, колодки изнашиваются быстрее. Проверяйте колодки примерно каждые 10 000 км. У новой колодки фрикционный слой около 10–12 мм; когда он стёрся до 3 мм — пора менять."),
                       ("h", "Передние или задние колодки"),
                       ("p", "Передние колодки обычно изнашиваются быстрее, потому что при торможении основная нагрузка приходится на переднюю ось. Колодки всегда меняют парой — на обоих колёсах одной оси. Диск меняют, если он сильно изношен, глубоко поцарапан или вызывает вибрацию."),
                       ("h", "Когда нельзя продолжать движение"),
                       ("p", "Если педаль проваливается до пола, подтекает тормозная жидкость или горит красный индикатор тормозов — остановитесь и не продолжайте движение. При необходимости вызовите {tow}."),
                       ("p", "Замена колодок на месте — {brakes}: приедем к вам, привезём колодки или установим ваши.")],
               faq=[("Что такое тормозные колодки?", "Металлическая пластина с фрикционным слоем, которую суппорт прижимает к тормозному диску, чтобы остановить машину."),
                    ("Сколько километров служат колодки?", "Точной цифры нет — зависит от стиля вождения и дорог. Проверяйте их примерно каждые 10 000 км и меняйте, когда фрикционный слой стёрся до 3 мм."),
                    ("Почему скрипят колодки?", "Часто это индикатор износа сообщает, что колодки стёрлись. Скрипеть могут и новые или загрязнённые колодки — лучше проверить.")]),
}

LINKS = {
    "ka": dict(tow=("ევაკუატორი", "evakuatori"), brakes=("ხუნდების შეცვლა გამოძახებით", "khundebis-shecvla")),
    "en": dict(tow=("tow truck", "evakuatori"), brakes=("mobile brake repair", "khundebis-shecvla"), seasonal=("seasonal tyre change on site", "sezonuri-saburavebis-shecvla"), mobile=("mobile tyre service", "modzravi-vulkanizacia"),
               rimweld=("rim welding", "diskis-dadugheba"), balancing=("wheel balancing", "balansireba"),
               pressure=("what the pressure should be", "blog:pressure"), tyres=("tyres by size", "hub"), wtyres=("winter tyres", "cat:winter")),
    "ru": dict(tow=("эвакуатор", "evakuatori"), brakes=("замена колодок с выездом", "khundebis-shecvla"), seasonal=("сезонная замена шин на месте", "sezonuri-saburavebis-shecvla"), mobile=("Мобильная вулканизация", "modzravi-vulkanizacia"),
               rimweld=("сварка дисков", "diskis-dadugheba"), balancing=("балансировка колёс", "balansireba"),
               pressure=("каким должно быть давление", "blog:pressure"), tyres=("шины по размерам", "hub"), wtyres=("зимние шины", "cat:winter")),
}


def link_fill(lang):
    out = {}
    for k, (text, target) in LINKS[lang].items():
        if target == "hub":
            href = T.LANG_HUB[lang]
        elif target.startswith("blog:"):
            href = url(target[5:], lang)
        elif target.startswith("cat:"):
            href = T.cat_url(target[4:], lang)
        else:
            href = svc(target, lang)
        out[k] = L(href, text)
    return out


CHECK, PLUS = T.CHECK, T.PLUS


def blocks_html(d, lang):
    fill = link_fill(lang)
    out = []
    for kind, val in d["blocks"]:
        if kind == "h":
            out.append(f'    <h2 class="mt-10 text-2xl font-bold font-head">{val}</h2>')
        elif kind == "p":
            out.append(f'    <p class="mt-4 leading-relaxed text-zinc-300">{val.format(**fill)}</p>')
        elif kind == "ul":
            out.append('    <ul class="mt-5 space-y-3">' + "".join(
                f'<li class="flex items-start gap-3"><span class="mt-0.5 text-brand">{CHECK}</span><span class="text-zinc-300">{x.format(**fill)}</span></li>' for x in val) + "</ul>")
        elif kind == "fig":
            img, alt, cap = d["fig"]
            out.append(f'    <figure class="mt-6 overflow-hidden rounded-2xl ring-1 ring-zinc-800"><picture><source srcset="/assets/{img}.avif" type="image/avif"><source srcset="/assets/{img}.webp" type="image/webp">'
                       f'<img loading="lazy" src="/assets/{img}.jpg" width="1680" height="1040" alt="{escape(alt)}" class="block h-auto w-full"></picture>'
                       f'<figcaption class="bg-zinc-900 px-4 py-3 text-sm text-zinc-400">{cap}</figcaption></figure>')
    return "\n".join(out)


def h1_of(key, lang):
    """Article H1; hand-written Georgian articles are read from their page."""
    if lang in A[key]:
        return A[key][lang]["h1"]
    page = (ROOT / "blog" / SLUGS[key]["ka"] / "index.html").read_text(encoding="utf-8")
    return re.sub(r"<[^>]+>", "", re.search(r"<h1[^>]*>(.*?)</h1>", page, re.S).group(1)).strip()


def article_page(key, lang):
    d = A[key][lang]
    U = UI[lang]
    urls = {l: url(key, l) for l in ("ka", "en", "ru")}
    img = d["fig"][0] if "fig" in d else IMG[key]
    hero = IMG[key]
    others = [k for k in ORDER if k != key]
    tips = "".join(f'<li><a href="{url(k, lang)}" class="flex items-center gap-2 text-zinc-300 hover:text-brand transition"><span aria-hidden="true">›</span><span>{h1_of(k, lang)}</span></a></li>' for k in others)
    services = "".join(f'<li><a href="{u}" class="text-zinc-300 hover:text-brand">{n}</a></li>' for n, u in SERVICES[lang])
    faq_html = '<div class="mt-5 space-y-3">' + "".join(
        f'<details class="group rounded-xl bg-zinc-900 ring-1 ring-zinc-800 open:ring-brand/50"><summary class="flex cursor-pointer items-center justify-between gap-4 p-5 font-semibold list-none"><span>{escape(q)}</span>{PLUS}</summary><p class="px-5 pb-5 -mt-1 text-zinc-400">{escape(x)}</p></details>'
        for q, x in d["faq"]) + "</div>"
    body = f"""<!-- Article header -->
<section class="mx-auto max-w-6xl px-4 pt-6">
  <div class="overflow-hidden rounded-3xl ring-1 ring-zinc-800">
    <div class="relative h-56 sm:h-72"><picture><source srcset="/assets/{hero}.avif" type="image/avif"><source srcset="/assets/{hero}.webp" type="image/webp"><img fetchpriority="high" src="/assets/{hero}.jpg" alt="{escape(d['h1'])}" class="absolute inset-0 h-full w-full object-cover"></picture><div class="absolute inset-0 bg-gradient-to-t from-zinc-950 via-zinc-950/50 to-transparent"></div></div>
  </div>
  <p class="mt-6 text-sm text-zinc-400"><time datetime="{DATES[key]}">{DATES[key]}</time> · {U['tips']}</p>
  <h1 class="mt-2 text-2xl font-bold font-head break-words sm:text-4xl">{d['h1']}</h1>
</section>

<!-- Content -->
<section class="mx-auto grid max-w-6xl gap-10 px-4 py-10 lg:grid-cols-3">
  <article class="lg:col-span-2">
{blocks_html(d, lang)}

    <h2 class="mt-10 text-2xl font-bold font-head">{U['faq']}</h2>
    {faq_html}

    <div class="mt-10 rounded-2xl bg-gradient-to-br from-brand/15 to-zinc-900 p-6 ring-1 ring-brand/30">
      <h2 class="text-xl font-bold font-head">{U['help_h']}</h2>
      <p class="mt-2 text-sm text-zinc-300">{U['help_p']}</p>
      <div class="mt-4 flex flex-wrap gap-3">{T.btn_call()}<a href="{svc(d['cta'], lang)}" class="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl bg-white/10 px-5 py-3 font-semibold ring-1 ring-white/20 hover:bg-white/20">{U['more']} →</a></div>
    </div>
  </article>

  <aside class="lg:col-span-1">
    <div class="sticky top-24 space-y-6">
      <div class="rounded-2xl bg-zinc-900 p-6 ring-1 ring-zinc-800">
        <h2 class="text-lg font-bold font-head">{U['other']}</h2>
        <ul class="mt-4 space-y-2.5 text-sm">{tips}</ul>
        <a href="{INDEX[lang]}" class="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-brand hover:text-amber-400">{U['all_tips']}</a>
      </div>
      <div class="rounded-2xl bg-zinc-900 p-6 ring-1 ring-zinc-800">
        <h2 class="text-lg font-bold font-head">{U['services']}</h2>
        <ul class="mt-4 space-y-2.5 text-sm">{services}</ul>
      </div>
    </div>
  </aside>
</section>
"""
    article = {"@context": "https://schema.org", "@type": "Article", "headline": d["h1"], "description": d["desc"],
               "image": [f"{SITE}/assets/{img}.jpg"], "datePublished": DATES[key], "dateModified": "2026-11-20", "inLanguage": lang,
               "mainEntityOfPage": {"@type": "WebPage", "@id": SITE + urls[lang]},
               "author": {"@type": "Organization", "name": "Vulkanizacia.ge", "url": SITE + "/"},
               "publisher": {"@type": "Organization", "name": "Vulkanizacia.ge", "logo": {"@type": "ImageObject", "url": f"{SITE}/assets/favicon.svg"}}}
    html = T.page(lang, url=urls[lang], title=d["title"], desc=d["desc"], keywords=d["keywords"], alternates=T.alts(urls), image=img,
                  schema=[article, T.faq_ld(d["faq"])], crumbs=[(U["home"], T.HOME[lang]), (U["tips"], INDEX[lang]), (d["h1"], None)],
                  body=body, nav_urls=urls)
    html = html.replace('<meta property="og:type" content="website">', '<meta property="og:type" content="article">')
    out = ROOT / urls[lang].strip("/") / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")


def index_page(lang):
    U = UI[lang]
    cards = "".join(f"""
    <article class="group overflow-hidden rounded-2xl bg-zinc-900 ring-1 ring-zinc-800 transition hover:ring-brand/60">
      <a href="{url(k, lang)}" class="block">
        <div class="relative h-44 overflow-hidden"><picture><source srcset="/assets/{IMG[k]}.avif" type="image/avif"><source srcset="/assets/{IMG[k]}.webp" type="image/webp"><img loading="lazy" src="/assets/{IMG[k]}.jpg" alt="{escape(A[k][lang]['h1'])}" class="h-full w-full object-cover transition duration-500 group-hover:scale-105"></picture></div>
        <div class="p-5">
          <h2 class="text-lg font-bold font-head">{A[k][lang]['h1']}</h2>
          <p class="mt-1.5 text-sm text-zinc-400">{A[k][lang]['card']}</p>
          <span class="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-brand">{U['read']} →</span>
        </div>
      </a>
    </article>""" for k in ORDER)
    body = f"""<section class="mx-auto max-w-6xl px-4 pt-6 pb-12">
  <h1 class="text-3xl font-bold font-head sm:text-4xl">{U['index_h1']}</h1>
  <p class="mt-3 max-w-2xl text-zinc-300">{U['index_lead']}</p>
  <div class="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">{cards}
  </div>
</section>
"""
    coll = {"@context": "https://schema.org", "@type": "CollectionPage", "name": U["index_h1"], "description": U["index_desc"], "inLanguage": lang,
            "url": SITE + INDEX[lang], "hasPart": [{"@type": "Article", "headline": A[k][lang]["h1"], "url": SITE + url(k, lang)} for k in ORDER]}
    html = T.page(lang, url=INDEX[lang], title=U["index_title"], desc=U["index_desc"], keywords="", alternates=T.alts(INDEX), image="service",
                  schema=[coll], crumbs=[(U["home"], T.HOME[lang]), (U["tips"], None)], body=body, nav_urls=INDEX)
    html = html.replace('<meta name="keywords" content="">\n', "")
    (ROOT / INDEX[lang].lstrip("/")).write_text(html, encoding="utf-8")


def ka_index_cards():
    """Hand-written Georgian blog index: add cards for generated Georgian articles (marker block, idempotent)."""
    arrow = '<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="1.7" stroke="currentColor" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3"/></svg>'
    cards = "".join(f"""
    <article class="group overflow-hidden rounded-2xl bg-zinc-900 ring-1 ring-zinc-800 transition hover:ring-brand/60">
      <a href="{url(k, 'ka')}" class="block">
        <div class="relative h-44 overflow-hidden"><picture><source srcset="/assets/{IMG[k]}.avif" type="image/avif"><source srcset="/assets/{IMG[k]}.webp" type="image/webp"><img loading="lazy" src="/assets/{IMG[k]}.jpg" alt="{escape(A[k]['ka']['h1'])}" class="h-full w-full object-cover transition duration-500 group-hover:scale-105"></picture></div>
        <div class="p-5">
          <h2 class="text-lg font-bold font-head">{A[k]['ka']['h1']}</h2>
          <p class="mt-1.5 text-sm text-zinc-400">{A[k]['ka']['card']}</p>
          <span class="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-brand">ვრცლად {arrow}</span>
        </div>
      </a>
    </article>""" for k in ORDER if k in GENERATED_KA)
    p = ROOT / "blog" / "index.html"
    s = p.read_text(encoding="utf-8")
    s = T.sync_block(s, "<!-- blog-ka-gen:start -->", "<!-- blog-ka-gen:end -->", cards + "\n    ", '    <article class="group')
    p.write_text(s, encoding="utf-8")


def patch_georgian():
    """Georgian originals: hreflang + language links to the translations (text untouched)."""
    pages = [(f"blog/{SLUGS[k]['ka']}/index.html", {l: url(k, l) for l in ("ka", "en", "ru")}) for k in ORDER if k not in GENERATED_KA] + [("blog/index.html", INDEX)]
    for rel, urls in pages:
        p = ROOT / rel
        s = p.read_text(encoding="utf-8")
        if 'hreflang="en"' not in s:
            alt = "".join(f'<link rel="alternate" hreflang="{h}" href="{SITE}{u}">' for h, u in T.alts(urls))
            s = re.sub(r'(<link rel="canonical"[^>]*>)', lambda m: m.group(1) + "\n" + alt, s, count=1)
        for lang, home in (("en", "/index-en.html"), ("ru", "/index-ru.html")):
            s = re.sub(r'href="' + re.escape(home) + r'"( class="px-(?:2|3) py-)', lambda m: f'href="{urls[lang]}"{m.group(1)}', s)
        p.write_text(s, encoding="utf-8")


def sync_sitemap():
    from datetime import date
    today = date.today().isoformat()
    u = lambda loc: f"  <url>\n    <loc>{SITE}{loc}</loc>\n    <lastmod>{today}</lastmod>\n    <priority>0.60</priority>\n  </url>\n"
    block = "\n" + u(INDEX["en"]) + u(INDEX["ru"]) + "".join(u(url(k, l)) for l in ("en", "ru") for k in ORDER) + "".join(u(url(k, "ka")) for k in ORDER if k in GENERATED_KA) + "  "
    p = ROOT / "sitemap.xml"
    s = p.read_text(encoding="utf-8")
    s = T.sync_block(s, "<!-- blog-i18n:start -->", "<!-- blog-i18n:end -->", block, "</urlset>")
    p.write_text(s, encoding="utf-8")


def main():
    for lang in ("en", "ru"):
        for k in ORDER:
            article_page(k, lang)
        index_page(lang)
    for k in GENERATED_KA:
        article_page(k, "ka")
    ka_index_cards()
    patch_georgian()
    T.ensure_nav()
    T.ensure_mobile_menu()
    sync_sitemap()
    print(f"blog: {len(ORDER)} articles + index in en/ru")


if __name__ == "__main__":
    main()
