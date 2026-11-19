"""Keyword landing pages for vulkanizacia.ge, each in ka/en/ru (from Google autocomplete research, 2026-11-20).

  - mobile tyre service:  ვულკანიზაცია ადგილზე / mobile tire repair / выездной шиномонтаж
  - all 22 Tbilisi districts listed on the mobile-service page (old per-district URLs redirect there)
  - nearby towns:         Rustavi (+ Ponichala), Mtskheta (+ Natakhtari, Saguramo, Tserovani)
  - tyre size calculator (interactive)
  - service: tyre pressure sensors (TPMS, "საბურავის ბლუთუზი")
All pages link to the ranked "ვულკანიზაცია გამოძახებით თბილისში" page (never duplicate it).
Existing pages are not changed except for added links (homepage block, service sidebars) and sitemap/llms blocks.

Run after build_tyres.py / build_blog_i18n.py and before build_md.py:  python3 tools/build_landings.py
"""
import re
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_tyres as T  # noqa: E402

ROOT, SITE, LANGS = T.ROOT, T.SITE, T.LANGS
TEL_FMT = T.TEL_FMT

# ranked pages we always link to (never duplicate)
ON_CALL = {"ka": "/vulkanizacia-gamodzaxebit-tbilisshi/", "en": "/vulcanization-on-call-tbilisi/", "ru": "/vulkanizaciya-po-vyzovu-tbilisi/"}
ON_CALL_TXT = {"ka": "ვულკანიზაცია გამოძახებით თბილისში", "en": "Vulcanization on call in Tbilisi", "ru": "Вулканизация по вызову в Тбилиси"}
H24 = {"ka": "/vulkanizacia-24-7-tbilisi/", "en": "/vulcanization-24-7-tbilisi/", "ru": "/vulkanizaciya-24-7-tbilisi/"}
H24_TXT = {"ka": "ვულკანიზაცია 24/7 თბილისი", "en": "Vulcanization 24/7 in Tbilisi", "ru": "Вулканизация 24/7 в Тбилиси"}

# ------------------------------------------------------------------ shared copy
C = {
    "ka": dict(home="მთავარი", onsite_h="რას ვაკეთებთ ადგილზე",
               onsite=["ნახვრეტის შეკეთება ადგილზე (ვულკანიზაცია)", "საბურავის შეცვლა ან სათადარიგოს დაყენება",
                       "ახალი ან მეორადი საბურავის მოტანა თქვენს ზომაში", "ბორბლების ბალანსირება", "წნევის შემოწმება და ჰაერის შევსება"],
               how="როგორ მუშაობს",
               steps=[("დაგვირეკეთ", f"დარეკეთ {TEL_FMT} ან გამოგვიგზავნეთ ლოკაცია WhatsApp-ით."), ("მოვალთ თქვენთან", "მოძრავი ვულკანიზაცია მოდის სრული აღჭურვილობით."),
                      ("შევაკეთებთ ან შევცვლით", "საბურავს ადგილზე შევაკეთებთ, შევცვლით და დავაბალანსებთ."), ("გზას განაგრძობთ", "ფასს წინასწარ შეგითანხმებთ — შემდეგ უსაფრთხოდ განაგრძობთ გზას.")],
               related="ასევე იხილეთ", areas_h="სად მოვდივართ", faq_h="ხშირად დასმული კითხვები",
               side_h="გჭირდებათ ვულკანიზაცია?", side_p="დაგვირეკეთ ან მოგვწერეთ — ვმუშაობთ 24/7.", wa="გამარჯობა, მჭირდება ვულკანიზაცია",
               tyres="საბურავები ზომით", calc="საბურავის კალკულატორი", sizes_h="პოპულარული ზომები",
               block_h="ვულკანიზაცია უბნებისა და ქალაქების მიხედვით", block_p="მოძრავი ვულკანიზაცია მოვა თქვენთან — თბილისის ყველა უბანსა და შემოგარენში."),
    "en": dict(home="Home", onsite_h="What we do on site",
               onsite=["Puncture repair on the spot", "Tire change or fitting the spare", "Bringing a new or used tire in your size",
                       "Wheel balancing", "Pressure check and inflation"],
               how="How it works",
               steps=[("Call us", f"Call {TEL_FMT} or send your location on WhatsApp."), ("We come to you", "The mobile tire service arrives fully equipped."),
                      ("Repair or replace", "We repair, replace and balance the tire on the spot."), ("Back on the road", "We agree the price in advance — then you continue safely.")],
               related="See also", areas_h="Where we come", faq_h="Frequently asked questions",
               side_h="Need a tire service?", side_p="Call or message us — we work 24/7.", wa="Hello, I need a mobile tire service",
               tyres="Tires by size", calc="Tire size calculator", sizes_h="Popular sizes",
               block_h="Mobile tire service by district and town", block_p="Our mobile tire service comes to you — in every Tbilisi district and nearby towns."),
    "ru": dict(home="Главная", onsite_h="Что мы делаем на месте",
               onsite=["Ремонт прокола на месте", "Замена колеса или установка запаски", "Привезём новую или б/у шину вашего размера",
                       "Балансировка колёс", "Проверка давления и подкачка"],
               how="Как это работает",
               steps=[("Позвоните", f"Позвоните {TEL_FMT} или отправьте геолокацию в WhatsApp."), ("Мы приедем", "Мобильная вулканизация приезжает со всем оборудованием."),
                      ("Отремонтируем или заменим", "Отремонтируем, заменим и отбалансируем колесо на месте."), ("Продолжайте путь", "Цену согласуем заранее — и вы безопасно продолжите путь.")],
               related="Смотрите также", areas_h="Куда мы выезжаем", faq_h="Частые вопросы",
               side_h="Нужен шиномонтаж?", side_p="Позвоните или напишите — работаем 24/7.", wa="Здравствуйте, нужен выездной шиномонтаж",
               tyres="Шины по размерам", calc="Шинный калькулятор", sizes_h="Популярные размеры",
               block_h="Шиномонтаж по районам и городам", block_p="Выездной шиномонтаж приедет к вам — в любой район Тбилиси и пригороды."),
}

# ------------------------------------------------------------------ places
TOWNS = {
    "rustavi": dict(slug=dict(ka="vulkanizacia-rustavshi", en="tire-repair-rustavi", ru="shinomontazh-rustavi"),
                    ka=dict(name="რუსთავი", h1="ვულკანიზაცია რუსთავში", title="ვულკანიზაცია რუსთავში — მოძრავი ვულკანიზაცია გამოძახებით",
                            desc=f"ვულკანიზაცია რუსთავში და რუსთავის გზაზე — მოძრავი ვულკანიზაცია მოვა თბილისიდან და საბურავს ადგილზე შეაკეთებს ან შეცვლის, 24/7. ☎ {TEL_FMT}",
                            keywords="ვულკანიზაცია რუსთავში, ვულკანიზაცია რუსთავი, მოძრავი ვულკანიზაცია რუსთავში, ვულკანიზაცია 24 7 რუსთავი, ვულკანიზაცია ფონიჭალა",
                            lead="გაგისკდათ საბურავი რუსთავში ან რუსთავის გზაზე? მოძრავი ვულკანიზაცია თბილისიდან მოვა თქვენთან და საბურავს ადგილზე შეაკეთებს ან შეცვლის.",
                            where="მოვდივართ რუსთავში და გზაზე თბილისიდან რუსთავამდე — ფონიჭალა, რუსთავის გზატკეცილი, ძველი და ახალი რუსთავი. მისვლის დრო მანძილზეა დამოკიდებული — დარეკვისას ზუსტად გეტყვით."),
                    en=dict(name="Rustavi", h1="Tire repair in Rustavi", title="Tire repair in Rustavi — mobile tire service from Tbilisi",
                            desc=f"Mobile tire repair in Rustavi and on the Rustavi road — we come from Tbilisi and repair or replace the tire on the spot, 24/7. ☎ {TEL_FMT}",
                            keywords="tire repair Rustavi, mobile tire service Rustavi, vulcanization Rustavi, flat tire Rustavi",
                            lead="Flat tire in Rustavi or on the Rustavi road? Our mobile tire service comes from Tbilisi and repairs or replaces the tire on the spot.",
                            where="We come to Rustavi and the road from Tbilisi — Ponichala, the Rustavi highway, Old and New Rustavi. Arrival time depends on the distance — we'll tell you exactly when you call."),
                    ru=dict(name="Рустави", h1="Шиномонтаж в Рустави", title="Шиномонтаж в Рустави — выездной, из Тбилиси",
                            desc=f"Выездной шиномонтаж в Рустави и на трассе Тбилиси — Рустави: приедем из Тбилиси, отремонтируем или заменим колесо на месте, 24/7. ☎ {TEL_FMT}",
                            keywords="шиномонтаж Рустави, выездной шиномонтаж Рустави, вулканизация Рустави",
                            lead="Пробили колесо в Рустави или по дороге в Рустави? Выездной шиномонтаж приедет из Тбилиси и отремонтирует или заменит шину на месте.",
                            where="Выезжаем в Рустави и на трассу Тбилиси — Рустави: Поничала, Руставское шоссе, Старый и Новый Рустави. Время приезда зависит от расстояния — точно скажем при звонке.")),
    "mtskheta": dict(slug=dict(ka="vulkanizacia-mcxetashi", en="tire-repair-mtskheta", ru="shinomontazh-mtskheta"),
                     ka=dict(name="მცხეთა", h1="ვულკანიზაცია მცხეთაში", title="ვულკანიზაცია მცხეთაში, ნატახტარსა და საგურამოში — გამოძახებით",
                             desc=f"ვულკანიზაცია მცხეთაში, ნატახტარში, საგურამოსა და წეროვანში — მოძრავი ვულკანიზაცია მოვა თბილისიდან და საბურავს ადგილზე შეაკეთებს ან შეცვლის, 24/7. ☎ {TEL_FMT}",
                             keywords="ვულკანიზაცია მცხეთაში, ვულკანიზაცია მცხეთა, ვულკანიზაცია ნატახტარი, ვულკანიზაცია საგურამო, მოძრავი ვულკანიზაცია მცხეთა",
                             lead="გაგისკდათ საბურავი მცხეთაში, ნატახტარში ან საგურამოში? მოძრავი ვულკანიზაცია თბილისიდან მოვა თქვენთან და საბურავს ადგილზე შეაკეთებს ან შეცვლის.",
                             where="მოვდივართ მცხეთაში, ნატახტარში, საგურამოში, წეროვანსა და თბილისი–მცხეთის გზაზე. მისვლის დრო მანძილზეა დამოკიდებული — დარეკვისას ზუსტად გეტყვით."),
                     en=dict(name="Mtskheta", h1="Tire repair in Mtskheta", title="Tire repair in Mtskheta, Natakhtari and Saguramo — mobile tire service",
                             desc=f"Mobile tire repair in Mtskheta, Natakhtari, Saguramo and Tserovani — we come from Tbilisi and repair or replace the tire on the spot, 24/7. ☎ {TEL_FMT}",
                             keywords="tire repair Mtskheta, tire repair Natakhtari, tire repair Saguramo, mobile tire service Mtskheta",
                             lead="Flat tire in Mtskheta, Natakhtari or Saguramo? Our mobile tire service comes from Tbilisi and repairs or replaces the tire on the spot.",
                             where="We come to Mtskheta, Natakhtari, Saguramo, Tserovani and the Tbilisi–Mtskheta road. Arrival time depends on the distance — we'll tell you exactly when you call."),
                     ru=dict(name="Мцхета", h1="Шиномонтаж в Мцхете", title="Шиномонтаж в Мцхете, Натахтари и Сагурамо — выездной",
                             desc=f"Выездной шиномонтаж в Мцхете, Натахтари, Сагурамо и Церовани: приедем из Тбилиси, отремонтируем или заменим колесо на месте, 24/7. ☎ {TEL_FMT}",
                             keywords="шиномонтаж Мцхета, шиномонтаж Натахтари, шиномонтаж Сагурамо, вулканизация Мцхета",
                             lead="Пробили колесо в Мцхете, Натахтари или Сагурамо? Выездной шиномонтаж приедет из Тбилиси и отремонтирует или заменит шину на месте.",
                             where="Выезжаем в Мцхету, Натахтари, Сагурамо, Церовани и на трассу Тбилиси — Мцхета. Время приезда зависит от расстояния — точно скажем при звонке.")),
}

MOBILE = dict(slug=dict(ka="vulkanizacia-adgilze", en="mobile-tire-repair-tbilisi", ru="vyezdnoy-shinomontazh-tbilisi"),
              ka=dict(kicker="მობილური ვულკანიზაცია", h1="ვულკანიზაცია ადგილზე",
                      title="ვულკანიზაცია ადგილზე თბილისში — მობილური ვულკანიზაცია 24/7",
                      desc=f"ვულკანიზაცია ადგილზე — მობილური ვულკანიზაცია თბილისში დღე და ღამე. მოვალთ თქვენთან, საბურავს შევაკეთებთ, შევცვლით და დავაბალანსებთ. ☎ {TEL_FMT}",
                      keywords="ვულკანიზაცია ადგილზე, მობილური ვულკანიზაცია, მობილური ვულკანიზაცია თბილისი, სადღეღამისო ვულკანიზაცია, ვულკანიზაციის გამოძახება, საბურავის შეცვლა ადგილზე",
                      lead="მობილური ვულკანიზაცია თბილისში — დღე და ღამე. ვულკანიზაციამდე მისვლა აღარ გჭირდებათ: მოვალთ იქ, სადაც ხართ, და საბურავს ადგილზე შევაკეთებთ ან შევცვლით.",
                      extra_h="სადღეღამისო ვულკანიზაცია",
                      extra="ვმუშაობთ 24/7 — ღამით, დასვენების დღეებსა და დღესასწაულებზეც. თბილისში ჩვეულებრივ 20-30 წუთში მოვდივართ, შემოგარენში კი — მანძილის მიხედვით.",
                      faq=[("რა არის მობილური ვულკანიზაცია?", "ეს არის ვულკანიზაცია, რომელიც თავად მოდის თქვენთან: ხელოსანი სრული აღჭურვილობით მოვა თქვენს ლოკაციაზე და საბურავს ადგილზე შეაკეთებს ან შეცვლის."),
                           ("ღამითაც მოდიხართ?", "დიახ, ვმუშაობთ 24/7, დასვენების და სადღესასწაულო დღეების ჩათვლით."),
                           ("რამდენ ხანში მოხვალთ?", "თბილისში ჩვეულებრივ 20-30 წუთში. შემოგარენში დრო მანძილზეა დამოკიდებული — დარეკვისას გეტყვით."),
                           ("რა ღირს ვულკანიზაცია ადგილზე?", "ფასი დამოკიდებულია სამუშაოსა და ლოკაციაზე. დაგვირეკეთ — ფასს წინასწარ შეგითანხმებთ.")]),
              en=dict(kicker="Mobile tire service", h1="Mobile tire repair in Tbilisi",
                      title="Mobile tire repair in Tbilisi — tire service on site 24/7",
                      desc=f"Mobile tire repair and tire service in Tbilisi, day and night. We come to you, repair, replace and balance tires on the spot. ☎ {TEL_FMT}",
                      keywords="mobile tire repair Tbilisi, tire repair Tbilisi, tire service Tbilisi, flat tire Tbilisi, puncture repair Tbilisi, 24 hour tire repair Tbilisi, vulkanizacia near me",
                      lead="A tire service that comes to you — day and night. No need to find a tire shop: we come to wherever you are and repair or replace the tire on the spot.",
                      extra_h="24-hour tire repair",
                      extra="We work 24/7 — at night, on weekends and holidays. In Tbilisi we usually arrive within 20–30 minutes; in nearby towns it depends on the distance. Good to know: in Georgia a tire repair shop is called “vulkanizacia” (ვულკანიზაცია) — that is us.",
                      faq=[("What is a mobile tire service?", "A tire service that comes to you: a technician arrives at your location with all the equipment and repairs or replaces the tire on the spot."),
                           ("Do you come at night?", "Yes, we work 24/7, including weekends and holidays."),
                           ("How fast do you arrive?", "Usually within 20–30 minutes in Tbilisi. In nearby towns it depends on the distance — we will tell you when you call."),
                           ("How much does mobile tire repair cost?", "It depends on the job and the location. Call us — we agree the price in advance.")]),
              ru=dict(kicker="Мобильный шиномонтаж", h1="Выездной шиномонтаж в Тбилиси",
                      title="Выездной шиномонтаж в Тбилиси — круглосуточно, 24/7",
                      desc=f"Выездной шиномонтаж в Тбилиси круглосуточно: приедем к вам, отремонтируем прокол, заменим и отбалансируем колесо на месте. ☎ {TEL_FMT}",
                      keywords="выездной шиномонтаж Тбилиси, мобильный шиномонтаж Тбилиси, круглосуточный шиномонтаж Тбилиси, шиномонтаж Тбилиси, шиномонтаж Грузия, вулканизация рядом, вулканизация на выезд",
                      lead="Шиномонтаж, который приезжает к вам, — днём и ночью. Не нужно искать мастерскую: приедем туда, где вы находитесь, и отремонтируем или заменим колесо на месте.",
                      extra_h="Круглосуточный шиномонтаж",
                      extra="Работаем 24/7 — ночью, в выходные и праздники. По Тбилиси обычно приезжаем за 20–30 минут, в пригороды — в зависимости от расстояния. Важно знать: в Грузии шиномонтаж называют «вулканизация» (ვულკანიზაცია) — это мы.",
                      faq=[("Что такое выездной шиномонтаж?", "Это шиномонтаж, который приезжает к вам: мастер со всем оборудованием приедет на место и отремонтирует или заменит шину."),
                           ("Вы работаете ночью?", "Да, работаем круглосуточно, 24/7, включая выходные и праздники."),
                           ("Как быстро приедете?", "По Тбилиси обычно за 20–30 минут. В пригороды время зависит от расстояния — скажем при звонке."),
                           ("Сколько стоит выездной шиномонтаж?", "Цена зависит от работы и места. Позвоните — согласуем цену заранее.")]))


def page_url(slug):
    return f"/{slug}/"


def tri(slugs):
    return {l: page_url(slugs[l]) for l in LANGS}


# (key, ka: name, loc, gen, landmarks; en: name, landmarks; ru: name, loc ("в …"), acc ("в …" direction), landmarks; slugs; outer = arrival depends on distance)
_D = [
    ("vake", ("ვაკე", "ვაკეში", "ვაკის", ["ჭავჭავაძის გამზირი", "აბაშიძის ქუჩა", "ვაკის პარკი", "ბაგები", "ლისის ტბის მიდამოები"]),
     ("Vake", ["Chavchavadze Avenue", "Abashidze Street", "Vake Park", "Bagebi", "the Lisi Lake area"]),
     ("Ваке", "Ваке", "Ваке", ["проспект Чавчавадзе", "улица Абашидзе", "парк Ваке", "Багеби", "район озера Лиси"]), "vakeshi", "vake", False),
    ("saburtalo", ("საბურთალო", "საბურთალოზე", "საბურთალოს", ["ვაჟა-ფშაველას გამზირი", "პეკინის გამზირი", "ყაზბეგის გამზირი", "ნუცუბიძის პლატო", "დელისი"]),
     ("Saburtalo", ["Vazha-Pshavela Avenue", "Pekini Avenue", "Kazbegi Avenue", "Nutsubidze Plateau", "Delisi"]),
     ("Сабуртало", "Сабуртало", "Сабуртало", ["проспект Важа-Пшавела", "проспект Пекина", "проспект Казбеги", "плато Нуцубидзе", "Делиси"]), "saburtaloze", "saburtalo", False),
    ("vera", ("ვერა", "ვერაზე", "ვერის", ["მელიქიშვილის გამზირი", "კოსტავას ქუჩა", "ვერის პარკი"]),
     ("Vera", ["Melikishvili Avenue", "Kostava Street", "Vera Park"]),
     ("Вера", "Вере", "Веру", ["проспект Меликишвили", "улица Костава", "парк Вера"]), "veraze", "vera", False),
    ("mtatsminda", ("მთაწმინდა", "მთაწმინდაზე", "მთაწმინდის", ["რუსთაველის გამზირი", "მთაწმინდის პარკი", "სოლოლაკი"]),
     ("Mtatsminda", ["Rustaveli Avenue", "Mtatsminda Park", "Sololaki"]),
     ("Мтацминда", "Мтацминде", "Мтацминду", ["проспект Руставели", "парк Мтацминда", "Сололаки"]), "mtatsmindaze", "mtatsminda", False),
    ("old-tbilisi", ("ძველი თბილისი", "ძველ თბილისში", "ძველი თბილისის", ["თავისუფლების მოედანი", "აბანოთუბანი", "მეიდანი"]),
     ("Old Tbilisi", ["Freedom Square", "Abanotubani", "Meidani"]),
     ("Старый Тбилиси", "Старом Тбилиси", "Старый Тбилиси", ["площадь Свободы", "Абанотубани", "Мейдани"]), "dzvel-tbilisshi", "old-tbilisi", False),
    ("avlabari", ("ავლაბარი", "ავლაბარში", "ავლაბრის", ["ავლაბრის მეტრო", "სამების საკათედრო ტაძარი", "მეტეხის მიდამოები"]),
     ("Avlabari", ["Avlabari metro", "Holy Trinity Cathedral (Sameba)", "the Metekhi area"]),
     ("Авлабари", "Авлабари", "Авлабари", ["метро Авлабари", "собор Самеба", "район Метехи"]), "avlabarshi", "avlabari", False),
    ("isani", ("ისანი", "ისანში", "ისნის", ["ისნის მეტრო", "ქეთევან წამებულის გამზირი", "ნავთლუღი", "ავლაბრის მიმართულება"]),
     ("Isani", ["Isani metro", "Ketevan Tsamebuli Avenue", "Navtlughi", "the Avlabari direction"]),
     ("Исани", "Исани", "Исани", ["метро Исани", "проспект Кетеван Цамебули", "Навтлуги", "направление Авлабари"]), "isanshi", "isani", False),
    ("samgori", ("სამგორი", "სამგორში", "სამგორის", ["სამგორის მეტრო", "კახეთის გზატკეცილი", "აეროპორტის გზატკეცილი"]),
     ("Samgori", ["Samgori metro", "Kakheti Highway", "the airport highway"]),
     ("Самгори", "Самгори", "Самгори", ["метро Самгори", "Кахетинское шоссе", "шоссе в аэропорт"]), "samgorshi", "samgori", False),
    ("varketili", ("ვარკეთილი", "ვარკეთილში", "ვარკეთილის", ["ვარკეთილის მეტრო", "ვარკეთილის მასივი", "ვაზისუბნის მიმართულება"]),
     ("Varketili", ["Varketili metro", "the Varketili residential area", "the Vazisubani direction"]),
     ("Варкетили", "Варкетили", "Варкетили", ["метро Варкетили", "массив Варкетили", "направление Вазисубани"]), "varketilshi", "varketili", False),
    ("chugureti", ("ჩუღურეთი", "ჩუღურეთში", "ჩუღურეთის", ["მარჯანიშვილის მოედანი", "აღმაშენებლის გამზირი", "სადგურის მოედანი"]),
     ("Chugureti", ["Marjanishvili Square", "Aghmashenebeli Avenue", "Station Square"]),
     ("Чугурети", "Чугурети", "Чугурети", ["площадь Марджанишвили", "проспект Агмашенебели", "Вокзальная площадь"]), "chughuretshi", "chugureti", False),
    ("didube", ("დიდუბე", "დიდუბეში", "დიდუბის", ["წერეთლის გამზირი", "დიდუბის მეტრო", "დიდუბის ავტოსადგური", "დიღმის მიმართულება"]),
     ("Didube", ["Tsereteli Avenue", "Didube metro", "Didube bus station", "the Dighomi direction"]),
     ("Дидубе", "Дидубе", "Дидубе", ["проспект Церетели", "метро Дидубе", "автостанция Дидубе", "направление Дигоми"]), "didubeshi", "didube", False),
    ("nadzaladevi", ("ნაძალადევი", "ნაძალადევში", "ნაძალადევის", ["ნაძალადევის მეტრო", "სანზონა", "გურამიშვილის მეტრო"]),
     ("Nadzaladevi", ["Nadzaladevi metro", "Sanzona", "Guramishvili metro"]),
     ("Надзаладеви", "Надзаладеви", "Надзаладеви", ["метро Надзаладеви", "Санзона", "метро Гурамишвили"]), "nadzaladevshi", "nadzaladevi", False),
    ("gldani", ("გლდანი", "გლდანში", "გლდანის", ["გლდანის მასივი", "ახმეტელის თეატრის მეტრო", "მუხიანი", "თბილისის ზღვის მიდამოები"]),
     ("Gldani", ["the Gldani residential area", "Akhmeteli Theatre metro", "Mukhiani", "the Tbilisi Sea area"]),
     ("Глдани", "Глдани", "Глдани", ["массив Глдани", "метро Театр Ахметели", "Мухиани", "район Тбилисского моря"]), "gldanshi", "gldani", False),
    ("dighomi", ("დიღომი", "დიღომში", "დიღმის", ["დიღმის მასივი", "დიდი დიღომი", "აღმაშენებლის ხეივანი"]),
     ("Dighomi", ["the Dighomi residential area", "Didi Dighomi", "Aghmashenebeli Alley"]),
     ("Дигоми", "Дигоми", "Дигоми", ["массив Дигоми", "Диди Дигоми", "аллея Агмашенебели"]), "dighomshi", "dighomi", False),
    ("temka", ("თემქა", "თემქაზე", "თემქის", ["თემქის მასივი", "თბილისის ზღვის მიმართულება"]),
     ("Temka", ["the Temka residential area", "the Tbilisi Sea direction"]),
     ("Темка", "Темке", "Темку", ["массив Темка", "направление Тбилисского моря"]), "temkaze", "temka", False),
    ("ortachala", ("ორთაჭალა", "ორთაჭალაში", "ორთაჭალის", ["გორგასლის ქუჩა", "ორთაჭალის ავტოსადგური", "ორთაჭალის ჰესის მიდამოები"]),
     ("Ortachala", ["Gorgasali Street", "Ortachala bus station", "the Ortachala HPP area"]),
     ("Ортачала", "Ортачале", "Ортачалу", ["улица Горгасали", "автостанция Ортачала", "район Ортачальской ГЭС"]), "ortachalashi", "ortachala", False),
    ("krtsanisi", ("კრწანისი", "კრწანისში", "კრწანისის", ["ფონიჭალა", "რუსთავის გზატკეცილი"]),
     ("Krtsanisi", ["Ponichala", "the Rustavi highway"]),
     ("Крцаниси", "Крцаниси", "Крцаниси", ["Поничала", "Руставское шоссе"]), "krtsanisshi", "krtsanisi", False),
    ("avchala", ("ავჭალა", "ავჭალაში", "ავჭალის", ["ზაჰესი", "მცხეთის მიმართულება"]),
     ("Avchala", ["Zahesi", "the Mtskheta direction"]),
     ("Авчала", "Авчале", "Авчалу", ["ЗАГЭС", "направление Мцхеты"]), "avchalashi", "avchala", False),
    ("lilo", ("ლილო", "ლილოში", "ლილოს", ["ლილოს ბაზრობა", "კახეთის გზატკეცილი", "აეროპორტის მიმართულება"]),
     ("Lilo", ["Lilo market", "Kakheti Highway", "the airport direction"]),
     ("Лило", "Лило", "Лило", ["рынок Лило", "Кахетинское шоссе", "направление аэропорта"]), "liloshi", "lilo", True),
    ("vazisubani", ("ვაზისუბანი", "ვაზისუბანში", "ვაზისუბნის", ["ვაზისუბნის მასივი", "ვარკეთილის მიმართულება"]),
     ("Vazisubani", ["the Vazisubani residential area", "the Varketili direction"]),
     ("Вазисубани", "Вазисубани", "Вазисубани", ["массив Вазисубани", "направление Варкетили"]), "vazisubanshi", "vazisubani", False),
    ("tskneti", ("წყნეთი", "წყნეთში", "წყნეთის", ["წყნეთის გზატკეცილი", "ბეთანიის მიმართულება"]),
     ("Tskneti", ["the Tskneti highway", "the Betania direction"]),
     ("Цхнети", "Цхнети", "Цхнети", ["Цхнетское шоссе", "направление Бетании"]), "tsknetshi", "tskneti", True),
    ("okrokana", ("ოქროყანა", "ოქროყანაში", "ოქროყანის", ["ოქროყანის გზა", "ტაბახმელას მიმართულება"]),
     ("Okrokana", ["the Okrokana road", "the Tabakhmela direction"]),
     ("Окрокана", "Окрокане", "Окрокану", ["дорога в Окрокану", "направление Табахмелы"]), "okroqanashi", "okrokana", True),
]
DISTRICTS = {k: dict(ka=ka, en=en, ru=ru, outer=outer, slug=dict(ka=f"vulkanizacia-{ks}", en=f"tire-repair-{es}", ru=f"shinomontazh-{es}"))
             for k, ka, en, ru, ks, es, outer in _D}


def town_copy(key, lang):
    t = TOWNS[key][lang]
    faq = {"ka": [(f"რამდენ ხანში ჩამოხვალთ ({t['name']})?", "მოვდივართ თბილისიდან, ამიტომ დრო მანძილსა და მოძრაობაზეა დამოკიდებული — დარეკვისას ზუსტად გეტყვით."),
                  ("ღამითაც მოდიხართ?", "დიახ, ვმუშაობთ 24/7."),
                  ("რა ღირს ვულკანიზაციის გამოძახება?", "ფასი დამოკიდებულია სამუშაოსა და მანძილზე — დაგვირეკეთ და წინასწარ შეგითანხმებთ.")],
           "en": [(f"How fast can you get to {t['name']}?", "We come from Tbilisi, so it depends on the distance and traffic — we'll tell you exactly when you call."),
                  ("Do you come at night?", "Yes, we work 24/7."),
                  ("How much does it cost?", "It depends on the job and the distance — call us and we'll agree the price in advance.")],
           "ru": [(f"Как быстро приедете ({t['name']})?", "Мы выезжаем из Тбилиси, поэтому время зависит от расстояния и дорожной ситуации — точно скажем при звонке."),
                  ("Приезжаете ночью?", "Да, работаем круглосуточно, 24/7."),
                  ("Сколько стоит выезд?", "Цена зависит от работы и расстояния — позвоните, и мы согласуем её заранее.")]}[lang]
    return dict(t, kicker={"ka": f"{t['name']} · 24/7", "en": f"{t['name']} · 24/7", "ru": f"{t['name']} · 24/7"}[lang], faq=faq)


AREA_T = {
    "ka": dict(all="თბილისის ყველა უბანი", h="ვულკანიზაცია თბილისის ყველა უბანში", p="მოვდივართ თბილისის ნებისმიერ უბანში:",
               eta="ქალაქში ჩვეულებრივ 20-30 წუთში მოვდივართ, გარეუბნებში (ლილო, წყნეთი, ოქროყანა) კი — მანძილის მიხედვით.",
               towns="ასევე მოვდივართ თბილისის შემოგარენში:",
               faq=("რომელ უბნებში მოდიხართ?", "თბილისის ყველა უბანში — ვაკე, საბურთალო, დიდუბე, გლდანი, ისანი, სამგორი, ვარკეთილი, დიღომი და სხვა — ასევე რუსთავსა და მცხეთაში.")),
    "en": dict(all="All Tbilisi districts", h="Tire repair in every Tbilisi district", p="We come to any district of Tbilisi:",
               eta="In the city we usually arrive within 20–30 minutes; in the outskirts (Lilo, Tskneti, Okrokana) it depends on the distance.",
               towns="We also come to nearby towns:",
               faq=("Which districts do you cover?", "Every district of Tbilisi — Vake, Saburtalo, Didube, Gldani, Isani, Samgori, Varketili, Dighomi and more — plus Rustavi and Mtskheta.")),
    "ru": dict(all="Все районы Тбилиси", h="Шиномонтаж во всех районах Тбилиси", p="Выезжаем в любой район Тбилиси:",
               eta="По городу обычно приезжаем за 20–30 минут, на окраины (Лило, Цхнети, Окрокана) — в зависимости от расстояния.",
               towns="Также выезжаем в пригороды:",
               faq=("В какие районы вы выезжаете?", "Во все районы Тбилиси — Ваке, Сабуртало, Дидубе, Глдани, Исани, Самгори, Варкетили, Дигоми и другие, а также в Рустави и Мцхету.")),
}


def district_names(lang):
    return [d[lang][0] for d in DISTRICTS.values()]


def districts_html(lang):
    A = AREA_T[lang]
    pills = "".join(f'<li class="rounded-full bg-zinc-900 px-3 py-1.5 text-sm text-zinc-200 ring-1 ring-zinc-800">{n}</li>' for n in district_names(lang))
    return (f'\n    <h2 class="mt-10 text-2xl font-bold font-head">{A["h"]}</h2>\n    <p class="mt-4 leading-relaxed text-zinc-300">{A["p"]}</p>\n'
            f'    <ul class="mt-4 flex flex-wrap gap-2">{pills}</ul>\n    <p class="mt-4 leading-relaxed text-zinc-300">{A["eta"]}</p>\n'
            f'    <p class="mt-4 leading-relaxed text-zinc-300">{A["towns"]}</p>\n    {chips(area_links(lang))}\n')


def area_links(lang):
    out = [(TOWNS[k][lang]["name"], page_url(TOWNS[k]["slug"][lang])) for k in TOWNS]
    return out


def chips(items):
    return '<div class="mt-4 flex flex-wrap gap-2">' + "".join(
        f'<a href="{u}" class="rounded-full bg-zinc-900 px-3 py-1.5 text-sm text-zinc-200 ring-1 ring-zinc-800 transition hover:text-brand hover:ring-brand/60">{n}</a>' for n, u in items) + "</div>"


def body_for(lang, c, urls, extra_html=""):
    U = C[lang]
    related = [(ON_CALL_TXT[lang], ON_CALL[lang]), (H24_TXT[lang], H24[lang]), (U["tyres"], T.LANG_HUB[lang]),
               (U["calc"], page_url(CALC["slug"][lang])), (MOBILE[lang]["h1"], page_url(MOBILE["slug"][lang]))]
    related = [(n, u) for n, u in related if u != urls[lang]]
    pop = "".join(T.chip(s, lang=lang) for s in T.POPULAR[:8])
    return f"""<!-- Hero card -->
<section class="mx-auto max-w-6xl px-4 pt-6">
  <div class="grid items-stretch gap-8 rounded-3xl bg-gradient-to-br from-zinc-900 to-zinc-900/40 p-6 ring-1 ring-zinc-800 sm:p-10 lg:grid-cols-2">
    <div class="flex flex-col">
      <p class="text-sm font-semibold uppercase tracking-wider text-brand">{c['kicker']}</p>
      <h1 class="mt-2 text-3xl font-bold font-head break-words sm:text-5xl">{c['h1']}</h1>
      <p class="mt-4 leading-relaxed text-zinc-300">{c['lead']}</p>
      <div class="mt-6 flex flex-wrap gap-3">{T.btn_call()}{T.btn_wa(U['wa'])}</div>
    </div>
    <div class="relative h-60 overflow-hidden rounded-2xl ring-1 ring-zinc-800 sm:h-72 lg:h-auto lg:min-h-80"><picture><source srcset="/assets/service.avif" type="image/avif"><source srcset="/assets/service.webp" type="image/webp"><img fetchpriority="high" src="/assets/service.jpg" alt="{escape(c['h1'])}" class="absolute inset-0 h-full w-full object-cover"></picture></div>
  </div>
</section>

<section class="mx-auto grid max-w-6xl gap-10 px-4 py-12 lg:grid-cols-3">
  <div class="lg:col-span-2">
    <h2 class="text-2xl font-bold font-head">{U['onsite_h']}</h2>
    {T.ul(U['onsite'])}
{extra_html}
    <h2 class="mt-10 text-2xl font-bold font-head">{U['how']}</h2>
    {T.steps(U['steps'])}

    <h2 class="mt-10 text-2xl font-bold font-head">{U['sizes_h']}</h2>
    <div class="mt-4 flex flex-wrap gap-2">{pop}</div>

    <h2 class="mt-10 text-2xl font-bold font-head">{U['related']}</h2>
    {T.ul([T.a(u, n) for n, u in related])}

    <h2 class="mt-10 text-2xl font-bold font-head">{U['faq_h']}</h2>
    {T.faq_html(c['faq'])}
  </div>
  <aside class="lg:col-span-1">
    <div class="sticky top-24 space-y-6">
      <div class="rounded-2xl bg-gradient-to-br from-brand/15 to-zinc-900 p-6 ring-1 ring-brand/30">
        <h2 class="text-xl font-bold font-head">{U['side_h']}</h2>
        <p class="mt-2 text-sm text-zinc-300">{U['side_p']}</p>
        <div class="mt-4 grid gap-2">{T.btn_call()}{T.btn_wa(U['wa'])}</div>
      </div>
      <div class="rounded-2xl bg-zinc-900 p-6 ring-1 ring-zinc-800">
        <h2 class="text-lg font-bold font-head">{U['areas_h']}</h2>
        {chips([(n, u) for n, u in [(AREA_T[lang]["all"], page_url(MOBILE["slug"][lang]))] + area_links(lang) if u != urls[lang]])}
      </div>
    </div>
  </aside>
</section>
"""


def write(lang, urls, c, body, schema_extra=()):
    U = C[lang]
    service = {"@context": "https://schema.org", "@type": "Service", "serviceType": c.get("svc_type", c["h1"]), "name": c["h1"],
               "description": c["desc"].split(" ☎")[0], "areaServed": c.get("area", {"@type": "City", "name": "Tbilisi"}), "provider": T.PROVIDER}
    html = T.page(lang, url=urls[lang], title=c["title"], desc=c["desc"], keywords=c["keywords"], alternates=T.alts(urls), image="service",
                  schema=[service, T.faq_ld(c["faq"]), *schema_extra], crumbs=[(U["home"], T.HOME[lang]), (c["h1"], None)], body=body, nav_urls=urls)
    u = urls[lang].lstrip("/")
    out = ROOT / (u if u.endswith(".html") else u + "index.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")


def build_mobile():
    urls = tri(MOBILE["slug"])
    for lang in LANGS:
        c = MOBILE[lang]
        U = C[lang]
        c = dict(c, faq=c["faq"] + [AREA_T[lang]["faq"]])
        extra = (f'\n    <h2 class="mt-10 text-2xl font-bold font-head">{c["extra_h"]}</h2>\n    <p class="mt-4 leading-relaxed text-zinc-300">{c["extra"]}</p>\n'
                 + districts_html(lang))
        write(lang, urls, c, body_for(lang, c, urls, extra))


def build_towns():
    for key, t in TOWNS.items():
        urls = tri(t["slug"])
        for lang in LANGS:
            c = town_copy(key, lang)
            extra = f'\n    <h2 class="mt-10 text-2xl font-bold font-head">{C[lang]["areas_h"]}</h2>\n    <p class="mt-4 leading-relaxed text-zinc-300">{c["where"]}</p>\n'
            c["area"] = {"@type": "City", "name": TOWNS[key]["en"]["name"]}
            write(lang, urls, c, body_for(lang, c, urls, extra))


# ------------------------------------------------------------------ tyre size calculator
CALC = dict(slug=dict(ka="saburavis-kalkulatori", en="tire-size-calculator", ru="shinnyy-kalkulyator"),
            ka=dict(kicker="ინსტრუმენტი", h1="საბურავის კალკულატორი",
                    title="საბურავის კალკულატორი — ზომების შედარება და სპიდომეტრის სხვაობა",
                    desc="საბურავის ზომის კალკულატორი: შეადარეთ ორი ზომა — სრული დიამეტრი, გვერდის სიმაღლე, სხვაობა პროცენტებში და სპიდომეტრის ცდომილება.",
                    keywords="საბურავის კალკულატორი, საბურავის ზომის კალკულატორი, საბურავის ზომების შედარება, სპიდომეტრის ცდომილება",
                    lead="შეადარეთ ახლანდელი და ახალი საბურავის ზომა: დიამეტრის სხვაობა და რას აჩვენებს სპიდომეტრი ახალ საბურავებზე.",
                    cur="ახლანდელი ზომა", new="ახალი ზომა", w="სიგანე", p="პროფილი", r="დისკი",
                    rows=("სრული დიამეტრი", "გვერდის სიმაღლე", "წრეწირის სიგრძე", "დიამეტრის სხვაობა"), unit="მმ",
                    speed="როცა სპიდომეტრი 100 კმ/სთ-ს აჩვენებს, რეალური სიჩქარეა", kmh="კმ/სთ",
                    ok="სხვაობა 3%-ის ფარგლებშია — ჩვეულებრივ დასაშვებია (შეამოწმეთ მწარმოებლის მითითება).",
                    bad="სხვაობა 3%-ზე მეტია — ასეთი ზომა არ არის რეკომენდებული.",
                    how_h="როგორ მუშაობს კალკულატორი",
                    how="სრული დიამეტრი = დისკის დიამეტრი + 2 × გვერდის სიმაღლე. გვერდის სიმაღლე = სიგანე × პროფილი / 100. მაგალითად, 205/55 R16-ის გვერდის სიმაღლეა ≈ 113 მმ, სრული დიამეტრი კი ≈ 632 მმ.",
                    rule_h="3%-ის წესი",
                    rule="ზომის შეცვლისას საბურავის სრული დიამეტრი სასურველია ქარხნულისგან 3%-ზე მეტად არ განსხვავდებოდეს — წინააღმდეგ შემთხვევაში იცვლება სპიდომეტრის ჩვენება და შეიძლება დაირღვეს ABS-ისა და სტაბილიზაციის სისტემების მუშაობა.",
                    faq=[("რას აჩვენებს საბურავის კალკულატორი?", "ორი ზომის სრულ დიამეტრს, გვერდის სიმაღლეს, სხვაობას პროცენტებში და რეალურ სიჩქარეს, როცა სპიდომეტრი 100 კმ/სთ-ს აჩვენებს."),
                         ("რამდენით შეიძლება განსხვავდებოდეს ახალი ზომა?", "სასურველია, სრული დიამეტრის სხვაობა 3%-ს არ აღემატებოდეს და ზომა ავტომობილის მწარმოებლის მიერ იყოს დაშვებული."),
                         ("სხვა ზომის საბურავს დამიყენებთ?", "დიახ — თუ ზომა დასაშვებია, მოგიტანთ და ადგილზე დაგიყენებთ. დაგვირეკეთ შერჩევისთვის.")]),
            en=dict(kicker="Tool", h1="Tire size calculator",
                    title="Tire size calculator — compare tire sizes and speedometer error",
                    desc="Tire size calculator: compare two sizes — overall diameter, sidewall height, difference in percent and speedometer error.",
                    keywords="tire size calculator, tire size comparison, tyre size calculator, speedometer error calculator",
                    lead="Compare your current and new tire size: the diameter difference and what your speedometer will show on the new tires.",
                    cur="Current size", new="New size", w="Width", p="Profile", r="Rim",
                    rows=("Overall diameter", "Sidewall height", "Circumference", "Diameter difference"), unit="mm",
                    speed="When the speedometer shows 100 km/h, the real speed is", kmh="km/h",
                    ok="The difference is within 3% — usually acceptable (check your car manufacturer's approved sizes).",
                    bad="The difference is more than 3% — this size is not recommended.",
                    how_h="How the calculator works",
                    how="Overall diameter = rim diameter + 2 × sidewall height. Sidewall height = width × profile / 100. For example, 205/55 R16 has a sidewall of ≈ 113 mm and an overall diameter of ≈ 632 mm.",
                    rule_h="The 3% rule",
                    rule="When changing tire size, the overall diameter should differ from the original by no more than 3% — otherwise the speedometer reading changes and ABS and stability control may not work as designed.",
                    faq=[("What does the tire size calculator show?", "The overall diameter and sidewall height of two sizes, the difference in percent and your real speed when the speedometer shows 100 km/h."),
                         ("How much can a new size differ?", "Ideally the overall diameter should differ by no more than 3%, and the size should be approved by the car manufacturer."),
                         ("Can you fit a different tire size?", "Yes — if the size is acceptable, we bring the tires and fit them on site. Call us for help choosing.")]),
            ru=dict(kicker="Инструмент", h1="Шинный калькулятор",
                    title="Шинный калькулятор — сравнение размеров шин и погрешность спидометра",
                    desc="Шинный калькулятор: сравните два размера — полный диаметр, высоту боковины, разницу в процентах и погрешность спидометра.",
                    keywords="шинный калькулятор, калькулятор шин, сравнение размеров шин, калькулятор размера шин, погрешность спидометра",
                    lead="Сравните текущий и новый размер шин: разницу в диаметре и что покажет спидометр на новых шинах.",
                    cur="Текущий размер", new="Новый размер", w="Ширина", p="Профиль", r="Диск",
                    rows=("Полный диаметр", "Высота боковины", "Длина окружности", "Разница диаметра"), unit="мм",
                    speed="Когда спидометр показывает 100 км/ч, реальная скорость", kmh="км/ч",
                    ok="Разница в пределах 3% — обычно допустимо (проверьте рекомендации производителя).",
                    bad="Разница больше 3% — такой размер не рекомендуется.",
                    how_h="Как работает калькулятор",
                    how="Полный диаметр = диаметр диска + 2 × высота боковины. Высота боковины = ширина × профиль / 100. Например, у 205/55 R16 высота боковины ≈ 113 мм, а полный диаметр ≈ 632 мм.",
                    rule_h="Правило 3%",
                    rule="При смене размера полный диаметр шины желательно менять не более чем на 3% от заводского — иначе меняются показания спидометра и может нарушиться работа ABS и системы стабилизации.",
                    faq=[("Что показывает шинный калькулятор?", "Полный диаметр и высоту боковины двух размеров, разницу в процентах и реальную скорость, когда спидометр показывает 100 км/ч."),
                         ("Насколько может отличаться новый размер?", "Желательно, чтобы полный диаметр отличался не более чем на 3%, а размер был допущен производителем автомобиля."),
                         ("Установите шины другого размера?", "Да — если размер допустим, привезём и установим на месте. Позвоните, поможем с подбором.")]))


def calc_widget(c):
    sel = "w-full rounded-xl bg-zinc-950 px-3 py-3 text-zinc-100 ring-1 ring-zinc-700 focus:outline-none focus:ring-brand"
    opts = lambda vals, cur: "".join(f'<option value="{v}"{" selected" if v == cur else ""}>{v}</option>' for v in vals)
    widths, profiles, rims = list(range(135, 345, 10)), list(range(25, 90, 5)), list(range(12, 25))

    def group(prefix, title, w, p, r):
        return f"""<fieldset class="rounded-2xl bg-zinc-900 p-5 ring-1 ring-zinc-800"><legend class="px-1 font-semibold">{title}</legend>
      <div class="mt-2 grid grid-cols-3 gap-3">
        <label class="flex flex-col gap-1 text-sm text-zinc-400">{c['w']}<select id="{prefix}w" class="{sel}">{opts(widths, w)}</select></label>
        <label class="flex flex-col gap-1 text-sm text-zinc-400">{c['p']}<select id="{prefix}p" class="{sel}">{opts(profiles, p)}</select></label>
        <label class="flex flex-col gap-1 text-sm text-zinc-400">{c['r']}<select id="{prefix}r" class="{sel}">{opts(rims, r)}</select></label>
      </div></fieldset>"""
    rows = "".join(f'<tr class="border-b border-zinc-800 last:border-0"><th class="py-3 pr-4 text-left font-medium text-zinc-400">{x}</th><td id="c{i}a" class="py-3 pr-4 font-semibold tabular-nums"></td><td id="c{i}b" class="py-3 font-semibold tabular-nums"></td></tr>' for i, x in enumerate(c["rows"]))
    return f"""
    <div id="tyre-calc" class="mt-2 grid gap-4 sm:grid-cols-2">{group('a', c['cur'], 205, 55, 16)}{group('b', c['new'], 225, 45, 17)}</div>
    <div class="mt-4 overflow-x-auto rounded-2xl bg-zinc-900 p-5 ring-1 ring-zinc-800"><table class="w-full text-sm"><thead><tr class="border-b border-zinc-700 text-zinc-400"><th></th><th class="py-2 pr-4 text-left font-medium">{c['cur']}</th><th class="py-2 text-left font-medium">{c['new']}</th></tr></thead><tbody>{rows}</tbody></table>
      <p class="mt-4 text-zinc-300">{c['speed']}: <strong id="cspeed" class="text-brand"></strong></p>
      <p id="cverdict" class="mt-2 font-semibold" aria-live="polite"></p></div>
    <script>
      (function () {{
        var T = {{ok: {repr(c['ok'])}, bad: {repr(c['bad'])}, mm: {repr(c['unit'])}, kmh: {repr(c['kmh'])}}};
        function v(id) {{ return +document.getElementById(id).value; }}
        function dims(p) {{ var w = v(p + 'w'), pr = v(p + 'p'), r = v(p + 'r'), sw = w * pr / 100, d = r * 25.4 + 2 * sw; return {{sw: sw, d: d, c: Math.PI * d}}; }}
        function set(id, t) {{ document.getElementById(id).textContent = t; }}
        function run() {{
          var a = dims('a'), b = dims('b'), diff = (b.d / a.d - 1) * 100;
          set('c0a', a.d.toFixed(0) + ' ' + T.mm); set('c0b', b.d.toFixed(0) + ' ' + T.mm);
          set('c1a', a.sw.toFixed(0) + ' ' + T.mm); set('c1b', b.sw.toFixed(0) + ' ' + T.mm);
          set('c2a', a.c.toFixed(0) + ' ' + T.mm); set('c2b', b.c.toFixed(0) + ' ' + T.mm);
          set('c3a', '—'); set('c3b', (diff > 0 ? '+' : '') + diff.toFixed(1) + '%');
          set('cspeed', (100 * b.d / a.d).toFixed(1) + ' ' + T.kmh);
          var el = document.getElementById('cverdict'), ok = Math.abs(diff) <= 3;
          el.textContent = ok ? T.ok : T.bad; el.className = 'mt-2 font-semibold ' + (ok ? 'text-emerald-400' : 'text-amber-400');
        }}
        document.querySelectorAll('#tyre-calc select').forEach(function (s) {{ s.addEventListener('change', run); }});
        run();
      }})();
    </script>
"""


def build_calc():
    urls = tri(CALC["slug"])
    for lang in LANGS:
        c = dict(CALC[lang])
        U = C[lang]
        body = f"""<section class="mx-auto max-w-4xl px-4 pt-6">
  <p class="text-sm font-semibold uppercase tracking-wider text-brand">{c['kicker']}</p>
  <h1 class="mt-2 text-3xl font-bold font-head sm:text-5xl">{c['h1']}</h1>
  <p class="mt-4 max-w-2xl leading-relaxed text-zinc-300">{c['lead']}</p>
{calc_widget(c)}
  <h2 class="mt-10 text-2xl font-bold font-head">{c['how_h']}</h2>
  <p class="mt-4 leading-relaxed text-zinc-300">{c['how']}</p>
  <h2 class="mt-10 text-2xl font-bold font-head">{c['rule_h']}</h2>
  <p class="mt-4 leading-relaxed text-zinc-300">{c['rule']}</p>
  <div class="mt-8 flex flex-col gap-4 rounded-3xl bg-gradient-to-br from-brand/15 to-zinc-900 p-6 ring-1 ring-brand/30 sm:flex-row sm:items-center sm:justify-between">
    <div><h2 class="text-xl font-bold font-head">{U['tyres']}</h2><p class="mt-1 text-zinc-300">{U['side_p']}</p></div>
    <div class="flex shrink-0 flex-wrap gap-3">{T.btn_call()}<a href="{T.LANG_HUB[lang]}" class="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl bg-white/10 px-5 py-3 font-semibold ring-1 ring-white/20 hover:bg-white/20">{U['tyres']} →</a></div>
  </div>
  <h2 class="mt-10 text-2xl font-bold font-head">{U['faq_h']}</h2>
  {T.faq_html(c['faq'])}
</section>
<div class="h-12"></div>
"""
        app = {"@context": "https://schema.org", "@type": "WebApplication", "name": c["h1"], "url": SITE + urls[lang], "applicationCategory": "UtilitiesApplication",
               "operatingSystem": "Any", "inLanguage": lang, "offers": {"@type": "Offer", "price": "0", "priceCurrency": "GEL"}, "description": c["desc"]}
        html = T.page(lang, url=urls[lang], title=c["title"], desc=c["desc"], keywords=c["keywords"], alternates=T.alts(urls), image="cover",
                      schema=[app, T.faq_ld(c["faq"])], crumbs=[(U["home"], T.HOME[lang]), (c["h1"], None)], body=body, nav_urls=urls)
        out = ROOT / urls[lang].strip("/") / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")


# ------------------------------------------------------------------ TPMS service (services/<slug>/ like the other services)
TPMS_SLUG = "saburavis-wnevis-sensori"
TPMS = {
    "ka": dict(kicker="სერვისი", h1="საბურავის წნევის სენსორი (ბლუთუზი)", svc_type="საბურავის წნევის სენსორის შეცვლა და დაპროგრამება",
               title="საბურავის წნევის სენსორი (ბლუთუზი) — შეცვლა და დაპროგრამება თბილისში",
               desc=f"საბურავის წნევის სენსორის (ბლუთუზის) შემოწმება, შეცვლა და დაპროგრამება თბილისში. შესაძლებლობა დამოკიდებულია მარკასა და მოდელზე — დაგვირეკეთ. ☎ {TEL_FMT}",
               keywords="საბურავის ბლუთუზი, საბურავის ბლუთუზის შეცვლა, საბურავის ბლუთუზის დაპროგრამება, საბურავის სენსორის შეცვლა, საბურავის წნევის სენსორი, TPMS",
               lead="დაფაზე საბურავის წნევის ნიშანი ანთია? შევამოწმებთ სენსორებს, საჭიროების შემთხვევაში შევცვლით და ავტომობილზე დავაპროგრამებთ. შესაძლებლობა დამოკიდებულია მარკასა და მოდელზე.",
               inc_h="რას მოიცავს სერვისი", inc=["წნევის სენსორების შემოწმება", "დაზიანებული ან დამჯდარი სენსორის შეცვლა", "ახალი სენსორის დაპროგრამება ავტომობილზე",
                                                "საბურავის შეცვლისას სენსორის ფრთხილად მოხსნა და დაყენება"],
               why_h="რატომ ანთია წნევის ნიშანი", why=["ერთ-ერთ საბურავში წნევა დაეცა — ჯერ წნევა შეამოწმეთ", "სენსორის ბატარეა დაჯდა (ჩვეულებრივ რამდენიმე წლის შემდეგ)",
                                                    "სენსორი დაზიანდა საბურავის შეცვლისას ან დარტყმისას", "ახალი სენსორი ან ბორბლები ავტომობილზე არ არის დაპროგრამებული"],
               note_h="მნიშვნელოვანია", note="სენსორის შეცვლა და დაპროგრამება დამოკიდებულია ავტომობილის მარკაზე, მოდელსა და წელზე. დაგვირეკეთ და გვითხარით მანქანის მონაცემები — გეტყვით, შეგვიძლია თუ არა დახმარება და რა ეღირება.",
               faq=[("რა არის საბურავის ბლუთუზი?", "ასე ხშირად უწოდებენ საბურავის წნევის სენსორს (TPMS) — მოწყობილობას დისკის შიგნით, რომელიც წნევას ზომავს და მონაცემებს უკაბელოდ გადასცემს ავტომობილს."),
                    ("ყველა მანქანის სენსორს შეცვლით?", "არა ყოველთვის — დამოკიდებულია მარკაზე, მოდელსა და წელზე. დაგვირეკეთ, შევამოწმებთ."),
                    ("რამდენ ხანს ძლებს სენსორი?", "სენსორს აქვს ჩაშენებული ბატარეა, რომელიც ჩვეულებრივ რამდენიმე წელიწადს ძლებს."),
                    ("ნიშანი ანთია, მაგრამ წნევა ნორმაშია — რა ვქნა?", "სავარაუდოდ სენსორის ან მისი დაპროგრამების პრობლემაა. დაგვირეკეთ — შევამოწმებთ.")]),
    "en": dict(kicker="Service", h1="Tire pressure sensors (TPMS)", svc_type="TPMS sensor replacement and programming",
               title="Tire pressure sensor (TPMS) replacement and programming in Tbilisi",
               desc=f"Tire pressure sensor (TPMS) check, replacement and programming in Tbilisi. Availability depends on the make and model — call us. ☎ {TEL_FMT}",
               keywords="TPMS Tbilisi, tire pressure sensor replacement, TPMS programming, tire pressure warning light",
               lead="Tire pressure warning light on? We check the sensors, replace them if needed and program them to your car. Availability depends on the make and model.",
               inc_h="What the service includes", inc=["Checking the pressure sensors", "Replacing a damaged or dead sensor", "Programming a new sensor to your car",
                                                     "Careful removal and refitting of sensors during a tire change"],
               why_h="Why the pressure light comes on", why=["Pressure dropped in one of the tires — check the pressure first", "The sensor battery is dead (usually after several years)",
                                                            "The sensor was damaged during a tire change or an impact", "A new sensor or new wheels are not programmed to the car"],
               note_h="Important", note="Sensor replacement and programming depend on the car's make, model and year. Call us with your car's details — we'll tell you whether we can help and what it costs.",
               faq=[("What is a TPMS sensor?", "A small sensor inside the wheel that measures tire pressure and sends it wirelessly to the car. In Georgia it is often called the tire “bluetooth”."),
                    ("Can you replace sensors on any car?", "Not always — it depends on the make, model and year. Call us and we'll check."),
                    ("How long does a sensor last?", "The sensor has a built-in battery that usually lasts several years."),
                    ("The light is on but the pressure is fine — what should I do?", "It is probably a sensor or programming issue. Call us — we'll check it.")]),
    "ru": dict(kicker="Услуга", h1="Датчики давления в шинах (TPMS)", svc_type="Замена и программирование датчиков давления в шинах",
               title="Датчики давления в шинах (TPMS) — замена и программирование в Тбилиси",
               desc=f"Проверка, замена и программирование датчиков давления в шинах (TPMS) в Тбилиси. Возможность зависит от марки и модели — позвоните. ☎ {TEL_FMT}",
               keywords="датчик давления в шинах, замена датчика давления шин, прописать датчики давления, TPMS Тбилиси",
               lead="Горит индикатор давления в шинах? Проверим датчики, при необходимости заменим и пропишем их в машину. Возможность зависит от марки и модели.",
               inc_h="Что входит в услугу", inc=["Проверка датчиков давления", "Замена повреждённого или разряженного датчика", "Программирование нового датчика в машину",
                                               "Аккуратный демонтаж и установка датчиков при замене шин"],
               why_h="Почему горит индикатор давления", why=["Упало давление в одной из шин — сначала проверьте давление", "Разрядилась батарейка датчика (обычно через несколько лет)",
                                                             "Датчик повреждён при шиномонтаже или ударе", "Новый датчик или новые колёса не прописаны в машину"],
               note_h="Важно", note="Замена и программирование датчиков зависят от марки, модели и года машины. Позвоните и назовите данные автомобиля — скажем, сможем ли помочь и сколько это стоит.",
               faq=[("Что такое датчик TPMS?", "Небольшой датчик внутри колеса, который измеряет давление в шине и по радиоканалу передаёт его в машину. В Грузии его часто называют «блютуз» шины."),
                    ("Вы меняете датчики на любой машине?", "Не всегда — это зависит от марки, модели и года. Позвоните, проверим."),
                    ("Сколько служит датчик?", "В датчике встроенная батарейка, которая обычно служит несколько лет."),
                    ("Индикатор горит, а давление в норме — что делать?", "Скорее всего, проблема в датчике или его программировании. Позвоните — проверим.")]),
}


def build_tpms():
    urls = {l: T.svc_url(TPMS_SLUG, l) for l in LANGS}
    for lang in LANGS:
        c = TPMS[lang]
        extra = (f'\n    <h2 class="mt-10 text-2xl font-bold font-head">{c["why_h"]}</h2>\n    {T.ul(c["why"])}\n'
                 f'    <h2 class="mt-10 text-2xl font-bold font-head">{c["note_h"]}</h2>\n    <p class="mt-4 leading-relaxed text-zinc-300">{c["note"]}</p>\n')
        cc = dict(c)
        body = body_for(lang, cc, urls, extra).replace(f'<h2 class="text-2xl font-bold font-head">{C[lang]["onsite_h"]}</h2>\n    {T.ul(C[lang]["onsite"])}',
                                                        f'<h2 class="text-2xl font-bold font-head">{c["inc_h"]}</h2>\n    {T.ul(c["inc"])}')
        write(lang, urls, cc, body)


# ------------------------------------------------------------------ links from existing pages (additive)
def sync_links():
    # homepages: one block with districts, towns, mobile page, calculator
    for lang, f in (("ka", "index.html"), ("en", "index-en.html"), ("ru", "index-ru.html")):
        U = C[lang]
        items = [(MOBILE[lang]["h1"], page_url(MOBILE["slug"][lang]))] + area_links(lang) + [(U["calc"], page_url(CALC["slug"][lang])), (TPMS[lang]["h1"], T.svc_url(TPMS_SLUG, lang))]
        block = f"""
<section class="mx-auto max-w-6xl px-4 pb-12">
  <h2 class="text-2xl font-bold font-head sm:text-3xl">{U['block_h']}</h2>
  <p class="mt-2 text-zinc-400">{U['block_p']}</p>
  {chips(items)}
</section>
"""
        p = ROOT / f
        s = p.read_text(encoding="utf-8")
        s = T.sync_block(s, "<!-- landings:start -->", "<!-- landings:end -->", block, "<!-- Why -->")
        p.write_text(s, encoding="utf-8")
    # "other services" sidebars on service pages: add the TPMS service
    for lang, fname in T.LANG_FILE.items():
        href = T.svc_url(TPMS_SLUG, lang)
        for p in sorted((ROOT / "services").glob(f"*/{fname}")):
            if p.parent.name == TPMS_SLUG:
                continue
            s = p.read_text(encoding="utf-8")
            m = re.search(r'(<h2 class="text-lg font-bold font-head">[^<]+</h2>\s*<ul class="mt-4 space-y-2.5 text-sm">)(.*?)(</ul>)', s, re.S)
            if not m or href in m.group(2):
                continue
            li = (f'<li><a href="{href}" class="flex items-center gap-2 text-zinc-300 hover:text-brand transition">'
                  '<svg class="h-4 w-4 text-brand shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="1.7" stroke="currentColor" aria-hidden="true">'
                  '<path stroke-linecap="round" stroke-linejoin="round" d="M8.288 15.038a5.25 5.25 0 0 1 7.424 0M5.106 11.856c3.807-3.808 9.98-3.808 13.788 0M1.924 8.674c5.565-5.565 14.587-5.565 20.152 0M12.53 18.22l-.53.53-.53-.53a.75.75 0 0 1 1.06 0Z"/></svg>'
                  f'<span>{TPMS[lang]["h1"]}</span></a></li>')
            s = s[:m.end(2)] + li + s[m.end(2):]
            p.write_text(s, encoding="utf-8")


def all_urls():
    out = []
    for group in [MOBILE["slug"], CALC["slug"]] + [t["slug"] for t in TOWNS.values()]:
        out += [page_url(group[l]) for l in LANGS]
    out += [T.svc_url(TPMS_SLUG, l) for l in LANGS]
    return out


def sync_sitemap_llms():
    from datetime import date
    today = date.today().isoformat()
    u = lambda loc: f"  <url>\n    <loc>{SITE}{loc}</loc>\n    <lastmod>{today}</lastmod>\n    <priority>0.80</priority>\n  </url>\n"
    p = ROOT / "sitemap.xml"
    s = p.read_text(encoding="utf-8")
    s = T.sync_block(s, "<!-- landings:start -->", "<!-- landings:end -->", "\n" + "".join(u(x) for x in all_urls()) + "  ", "</urlset>")
    p.write_text(s, encoding="utf-8")
    p = ROOT / "llms.txt"
    s = p.read_text(encoding="utf-8")
    block = ("\n## Mobile tire service by area (ვულკანიზაცია ადგილზე / выездной шиномонтаж)\n"
             f"- Mobile tire service, 24/7: {SITE}/{MOBILE['slug']['ka']}/ · EN {SITE}/{MOBILE['slug']['en']}/ · RU {SITE}/{MOBILE['slug']['ru']}/\n"
             + f"- Districts covered (all Tbilisi, one page): {', '.join(district_names('en'))}\n"
             + f"- Rustavi and Ponichala: {SITE}/{TOWNS['rustavi']['slug']['ka']}/\n"
             + f"- Mtskheta, Natakhtari, Saguramo, Tserovani: {SITE}/{TOWNS['mtskheta']['slug']['ka']}/\n"
             + f"- Tire size calculator: {SITE}/{CALC['slug']['ka']}/ · EN {SITE}/{CALC['slug']['en']}/ · RU {SITE}/{CALC['slug']['ru']}/\n"
             + f"- Tire pressure sensors (TPMS) — depends on make and model: {SITE}{T.svc_url(TPMS_SLUG, 'ka')}\n")
    s = T.sync_block(s, "<!-- landings:start -->", "<!-- landings:end -->", block, "## Service area") if "## Service area" in s else s + "\n<!-- landings:start -->" + block + "<!-- landings:end -->\n"
    p.write_text(s, encoding="utf-8")


def write_district_redirects():
    """Separate district pages (live < 1 hour on 2026-11-20) were merged into the mobile-service page; keep their URLs working."""
    import shutil
    for d in DISTRICTS.values():
        for lang in LANGS:
            new = page_url(MOBILE["slug"][lang])
            folder = ROOT / d["slug"][lang]
            if folder.is_dir():
                shutil.rmtree(folder)
            folder.mkdir()
            (folder / "index.html").write_text(
                f'<!DOCTYPE html>\n<html><head><meta charset="utf-8"><title>Redirect</title>'
                f'<link rel="canonical" href="{SITE}{new}"><meta name="robots" content="noindex, follow">'
                f'<meta http-equiv="refresh" content="0; url={new}"></head>'
                f'<body><a href="{new}">{SITE}{new}</a></body></html>\n', encoding="utf-8")


def main():
    build_mobile()
    write_district_redirects()
    build_towns()
    build_calc()
    build_tpms()
    sync_links()
    sync_sitemap_llms()
    T.ensure_nav()
    T.ensure_mobile_menu()
    print(f"landings: {len(all_urls())} pages (ka/en/ru)")


if __name__ == "__main__":
    main()
