# encoding=utf-8
import django

django.setup()
from sefaria.model import *
from sefaria.system.exceptions import BookNameError

# root = library.get_toc_tree().get_root()

def moveIndexInto(index, cat):
    if not isinstance(index, Index):
        try:
            index = library.get_index(index)
        except BookNameError:
            print("Can not find: {}".format(index))
            return
    if not isinstance(cat, Category):
        cat = Category().load({"path": cat})

    index.categories = cat.path[:]
    print("Moving - " + index.get_title() + " to " + str(index.categories) + " (moveIndexInto)")
    index.save(override_dependencies=True)


def moveCategoryInto(cat, parent):
    """
    c = Category().load({'path': ["Tanaitic", "Minor Tractates"]})
    p = Category().load({"path": ["Talmud", "Bavli"]})
    moveCategoryInto(c, p)

    if parent is None, move to root.

    :param cat:
    :param parent:
    :return:
    """
    if not isinstance(cat, Category):
        cat = Category().load({"path": cat})
    assert isinstance(cat, Category)

    if not isinstance(parent, Category) and parent is not None:
        parent = Category().load({"path": parent})
    assert isinstance(parent, Category) or parent is None


    old_category_path = cat.path[:]
    old_parent_path = cat.path[:-1]
    new_parent_path = parent.path[:] if parent else []

    # move all matching categories
    clauses = [{"path." + str(i): cname} for i, cname in enumerate(old_category_path)]
    query = {"$and": clauses}
    old_parent_length = len(old_parent_path)
    for cat in CategorySet(query):
        # replace old_parent_path with new_parent_path
        cat.path = new_parent_path + cat.path[old_parent_length:]
        print("Saving moved category - " + str(cat.path))
        cat.save(override_dependencies=True)

    # move all matching Indexes
    clauses = [{"categories." + str(i): cname} for i, cname in enumerate(old_category_path)]
    query = {"$and": clauses}
    for ind in IndexSet(query):
        assert isinstance(ind, Index)
        ind.categories = new_parent_path + ind.categories[old_parent_length:]
        print("Moving - " + ind.get_title() + " to " + str(ind.categories) + " (moveCategoryInto)")
        ind.save(override_dependencies=True)

    """
     Handle commentary on parallel trees separately.
     "title": "Commentary of Chida on Tractate Gerim",
     "categories": [
     "Tanaitic",
     "Commentary",
     "Commentary of Chida",
     "Minor Tractates"
     ],
    """


def create_category(path, en=None, he=None):
    c = Category()
    if not Term().load({"name": path[-1]}):
        if en is None or he is None:
            raise Exception("Need term names for {}".format(path[-1]))
        print("adding term for " + en)
        term = Term()
        term.name = en
        term.add_primary_titles(en, he)
        term.scheme = "toc_categories"
        term.save()
    c.add_shared_term(path[-1])
    c.path = path
    c.lastPath = path[-1]
    print("Creating - {}".format(" / ".join(c.path)))
    c.save(override_dependencies=True)
    return c


def change_term_hebrew(en_primary, new_he):
    t = Term().load({"name": en_primary})
    assert t
    old_primary = t.get_primary_title("he")
    t.add_title(new_he, "he", True, True)
    t.remove_title(old_primary, "he")
    t.save()


# Change Hebrew primaries for categories
for k, he in [
    ("Aggadic Midrash", 'מדרשי אגדה'),
    ("Halachic Midrash", 'מדרשי הלכה'),
    ("Reference", "מילונים וספרי יעץ"),
    ("Dictionary", "מילונים")
]:
    change_term_hebrew(k, he)

i = library.get_index("Zohar")
i.nodes.add_title("ספר הזהר", "he", True, True)
i.save(override_dependencies=True)

moveIndexInto("Seder Olam Zutta", ["Midrash", "Aggadic Midrash"])
sor = create_category(["Midrash", "Aggadic Midrash", "Seder Olam Rabbah"], "Seder Olam Rabbah", "סדר עולם רבה")
moveIndexInto("Seder Olam Rabbah", sor)

sor_com = create_category(["Midrash", "Aggadic Midrash", "Seder Olam Rabbah", "Commentary"])
for comm in ["Vilna_Gaon_on_Seder_Olam_Rabbah",
             "Meir Ayin on Seder Olam Rabbah",
             "Yaakov Emden on Seder Olam Rabbah"]:
    moveIndexInto(comm, sor_com)

for n, o in [("Esther Rabbah", 10), ("Eichah Rabbah", 8)]:
    i = library.get_index(n)
    i.order = [o]
    i.save(override_dependencies=True)


### The rest of the minor tractates -> Talmud/Bavli
c = Category().load({'path': ["Tanaitic", "Minor Tractates"]})
p = Category().load({"path": ["Talmud", "Bavli"]})
moveCategoryInto(c, p)


#        "Tanaitic",         "Commentary",         "Nahalat Yaakov",         "Minor Tractates"
#   =>   "Talmud",      "Bavli",    "Commentary on Minor Tractates",  "Nahalat Yaakov"
c = create_category(["Talmud", "Bavli", "Commentary on Minor Tractates"], "Commentary on Minor Tractates", "מפרשים על המסכתות הקטנות")

library.rebuild(include_toc=True)
tc = Category().load({'path': ["Tanaitic", "Commentary"]}).get_toc_object()
for kid in tc.children:
    c = create_category(["Talmud", "Bavli", "Commentary on Minor Tractates", kid.get_primary_title()])
    for i in [n.get_index_object() for n in kid.get_leaf_nodes()]:
        moveIndexInto(i,c)

library.rebuild(include_toc=True)

cs = CategorySet({"$and": [{"path.0": "Tanaitic"}, {"path.1": "Commentary"}]})
for c in cs:
    if len(c.path) >= 4:
        c.delete(override_dependencies=True)

library.rebuild(include_toc=True)

for c in cs:
    if len(c.path) == 3:
        c.delete(override_dependencies=True)


### Tosefta -> New top level category
c = Category().load({"path": ["Tanaitic", "Tosefta"]})
moveCategoryInto(c, None)


library.rebuild(include_toc=True)

# Remove Modern Works
c = Category().load({"path": ["Modern Works", "English Explanation of Mishnah"]})
p = Category().load({"path": ["Mishnah", "Commentary"]})
moveCategoryInto(c, p)

# Shoel uMeshiv to subcat
c = create_category(["Responsa", "Shoel uMeshiv"], en="Shoel uMeshiv", he="שואל ומשיב")
ts = ["Shoel uMeshiv Mahadura I",
      "Shoel uMeshiv Mahadura II",
      "Shoel uMeshiv Mahadura III",
      "Shoel uMeshiv Mahadura IV",
      "Shoel uMeshiv Mahadura V",
      "Shoel uMeshiv Mahadura VI"]

for t in ts:
    moveIndexInto(t, c)

# Contemporary .. into Halacha
c = create_category(["Halakhah", "Contemporary Halakhic Problems"], en="Contemporary Halakhic Problems",
                    he='בעיות הלכתיות עכשוויות')
ts = [
    'Contemporary Halakhic Problems, Vol I',
    'Contemporary Halakhic Problems, Vol II',
    'Contemporary Halakhic Problems, Vol III',
    'Contemporary Halakhic Problems, Vol IV',
    'Contemporary Halakhic Problems, Vol V',
    'Contemporary Halakhic Problems, Vol VI']
for t in ts:
    moveIndexInto(t, c)

# Gray Matter into Halacha
c = create_category(["Halakhah", "Gray Matter"], en="Gray Matter", he='גריי מאטר')
ts = [
    'Gray Matter I',
    'Gray Matter II',
    'Gray Matter III',
    'Gray Matter IV',
]
for t in ts:
    moveIndexInto(t, c)

# Marei HaBazak to subcat
c = create_category(["Responsa", "B'Mareh HaBazak"], en="B'Mareh HaBazak", he='שו"ת במראה הבזק')
mb = {"B'Mareh HaBazak Volume I": 1,
      "B'Mareh HaBazak Volume III": 3,
      "B'Mareh HaBazak Volume IV": 4,
      "B'Mareh HaBazak Volume IX": 9,
      "B'Mareh HaBazak Volume V": 5,
      "B'Mareh HaBazak Volume VI": 6,
      "B'Mareh HaBazak Volume VII": 7,
      "B'Mareh HaBazak Volume VIII": 8}

for t, o in mb.items():
    i = library.get_index(t)
    i.order = [o]
    moveIndexInto(i, c)  # saves i

# Daf Shevui -> Talmud Commentary
c = create_category(["Talmud", "Bavli", "Commentary", "Daf Shevui"], en="Daf Shevui", he="דף שבועי")
ts = ["Daf Shevui to Avodah Zarah",
      "Daf Shevui to Ketubot",
      "Daf Shevui to Kiddushin",
      "Daf Shevui to Megillah",
      "Daf Shevui to Sukkah"]

for t in ts:
    moveIndexInto(t, c)

moveIndexInto("A New Israeli Commentary on Pirkei Avot", ["Mishnah", "Commentary"])  # deeper cat?

c = create_category(["Reference", "Grammar"])
ts = ["Sefer haBachur", "Mahberet Menachem", "Sefat Yeter"]
for t in ts:
    moveIndexInto(t, c)

# Jastrow, Klein Dictionary, Otzar Laazei Rashi  => Reference, Dictionary
c = create_category(["Reference", "Dictionary"])
ts = ['Jastrow', 'Klein Dictionary', 'Otzar Laazei Rashi']
for t in ts:
    moveIndexInto(t, c)

# Into reference
c = Category().load({"path": "Reference"})
ts = ["The Jewish Spiritual Heroes", "Ein Zocher", "Devash Lefi", "Midbar Kedemot", "Imrei Binah"]
for t in ts:
    moveIndexInto(t, c)

#  Second Temple
stw = create_category(["Second Temple"], "Second Temple", "ספרות בית שני")

moveCategoryInto(["Apocrypha"], stw)

cat_ph = create_category(["Second Temple", "Philo"], "Philo", "פילון האלכסנדרוני")
for t in ['The Midrash of Philo',
                 'On the Life of Moses',
                 ]:
    moveIndexInto(t, cat_ph)

cat_jo = create_category(["Second Temple", "Josephus"], "Josephus", "יוסף בן מתתיהו")
for t in ['The Antiquities of the Jews',
                 'The War of the Jews',
          'Against Apion']:
    moveIndexInto(t, cat_jo)

moveIndexInto("Megillat Taanit", ["Second Temple"])


library.rebuild(include_toc=True)


# Rename Philosophy -> Jewish Thought
ph = Term().load({"name": "Philosophy"})
ph.remove_title("מחשבת ישראל", "he")
ph.add_title("פילוסופיה", "he", True, True)
ph.save()

jt = Term().load({"name": "Jewish Thought"})
jt.remove_title("מחשבה יהודית", "he")
jt.add_title("מחשבת ישראל", "he", True, True)
jt.save()

# Change the philo cat itself
phc = Category().load({"path": ["Philosophy"]})
phc.change_key_name("Jewish Thought")
phc.save(override_dependencies=True)

# move all matching categories
for cat in CategorySet({"path.0": "Philosophy"}):
    # replace old_parent_path with new_parent_path
    cat.path = ["Jewish Thought"] + cat.path[1:]
    print("Saving moved category - " + str(cat.path))
    cat.save(override_dependencies=True)

# move all matching Indexes
for ind in IndexSet({"categories.0": "Philosophy"}):
    assert isinstance(ind, Index)
    ind.categories = ["Jewish Thought"] + ind.categories[1:]
    print("Moving - " + ind.get_title() + " to " + str(ind.categories))
    ind.save(override_dependencies=True)

# Move Works of Eliezer Berkovits -> Jewish Thought
c = Category().load({"path": ["Modern Works", "Works of Eliezer Berkovits"]})
p = Category().load({"path": ["Jewish Thought"]})
moveCategoryInto(c, p)

library.rebuild(include_toc=True)

c = Category().load({"path": ["Jewish Thought", "Works of Eliezer Berkovits"]})
c.change_key_name("Eliezer Berkovits")
c.save(override_dependencies=True)

# move all matching Indexes
for ind in IndexSet({"categories.1": "Works of Eliezer Berkovits"}):
    assert isinstance(ind, Index)
    ind.categories = ["Jewish Thought", "Eliezer Berkovits"]
    print("Moving - " + ind.get_title() + " to " + str(ind.categories))
    ind.save(override_dependencies=True)

cat_rishonim = create_category(["Jewish Thought", "Rishonim"], "Rishonim", "ראשונים")
books_rishonim = ["HaEmunot veHaDeot", "Eight Chapters",
                  "Guide for the Perplexed",
                  "Treatise on Logic",
                  "Darashos HaRan",
                  "Ma'amar al Yishmael",
                  "Akeidat Yitzchak",
                  "Sefer Kuzari",
                  "Sefer HaIkkarim",
                  "Ohr Hashem",
                  "The Wars of the Lord",
                  "Minhat Kenaot",
                  "Yesod Mora",
                  ]

cat_duties = create_category(["Jewish Thought", "Rishonim", "Duties of the Heart"], "Duties of the Heart", "חובות הלבבות")
books_duties = ["Duties of the Heart",
                "Duties of the Heart (abridged)"]

cat_acharonim = create_category(["Jewish Thought", "Acharonim"], "Acharonim", "אחרונים")
books_acharonim = ["Derech Hashem",
                   "Essay on Fundamentals",
                   "Vilna Gaon's students letter to the Lost Tribes of Israel",
                   "Nefesh HaChayim",
                   "Kol HaTor",
                   "Torat HaOlah",
                   "Derush Chidushei HaLevana",
                   "The Third Beit HaMikdash"]

cat_kook = create_category(["Jewish Thought", "Rav Kook"], "Rav Kook", "כתבי הרב קוק")
books_kook = ["Orot",
              "Orot HaKodesh",
              "Orot HaTorah",
              "For the Perplexed of the Generation",
              "Maamar Hador",
              "Shmonah Kvatzim",
              "Midbar Shur"]

cat_modern = create_category(["Jewish Thought", "Modern"], "Modern", "ספרות מודרנית")
books_modern = ["Nineteen Letters",
                "Sefer Yesodei HaTorah",
                "Gan Naul",
                "Words of Peace and Truth",
                "Kol Dodi Dofek",
                "Hegyonei Uziel",
                "Revealment and Concealment in Language",
                "Halacha and Aggadah"]

for cat, books in [
    (cat_kook, books_kook),
    (cat_rishonim, books_rishonim),
    (cat_duties, books_duties),
    (cat_acharonim, books_acharonim),
    (cat_modern, books_modern)
]:
    for book in books:
        i = library.get_index(book)
        if not i:
            print("Didn't find book: {}".format(book))
            continue
        moveIndexInto(i, cat)

p = Category().load({"path": ["Jewish Thought"]})
for t in ["Ali Be'er on Revealment and Concealment in Language",
      'Bein HaShitin on Halacha and Aggadah',
      'Commentaries on Revealment and Concealment in Language']:
    moveIndexInto(t, p)

p = create_category(["Jewish Thought", "Rishonim", "Duties of the Heart", "Commentary"])
for t in [
    "Tov haLevanon",
    "Pat Lechem",
    "Marpeh la'Nefesh"
]:
    moveIndexInto(t, p)


moveIndexInto("Ein Ayah", ["Talmud", "Bavli", "Commentary"])

moveIndexInto('Abraham Cohen Footnotes to the English Translation of Masechet Berakhot',
              ["Talmud", "Bavli", "Commentary"])

# Reorg Halacha
cat_ivh = create_category(["Halakhah", "Issur v'Heter"], "Issur v'Heter", "איסור והיתר")
books_ivh = ["Issur V'Heter L'Rabbeinu Yerucham",
             'Issur veHeter leRashi',
             'Torat HaBayit HaAroch',
             'Torat HaBayit HaKatzar']

cat_mitzvot = create_category(["Halakhah", "Sifrei Mitzvot"], "Sifrei Mitzvot", "ספרי מצוות")
books_mitzvot = ['Sefer Hamitzvot of Rasag',
                 'Sefer Mitzvot Gadol',
                 'Sefer Mitzvot Katan',
                 'Sefer HaMitzvot HaKatzar',
                 'Sefer HaChinukh',
                 'Minchat Chinukh',
                 'Sefer Yereim',
                 'Kitzur Sefer Haredim of Rabbi Elazar Azcari']

cat_mono = create_category(["Halakhah", "Monographs"], "Monographs", "ספרי מונוגרפיה")
books_mono = ['Chofetz Chaim',
              'The Sabbath Epistle',
              'Treasures Hidden in the Sand',
              'Bedikat HaSakin',
              "Dina d'Garmei",
              'Ein HaTekhelet',
              'Gevurat Anashim',
              'Hilchos Talmud Torah',
              'Keset HaSofer',
              'Piskei Challah',
              'Ptil Tekhelet',
              "Sha'ar HaMayim HaAroch",
              "Sha'ar HaMayim HaKatzar",
              'Shulchan Shel Arba',
              'Care of the Critically Ill',
              "Ahavat Chesed",
              "Shev Shmat'ta",
              'Mateh Efrayim',
              'Simla Chadasha']

cat_other_r = create_category(["Halakhah", "Other Rishonim"], "Other Rishonim", "ראשונים נוספים")
books_other_r = ['Ohr Zarua',
                 'Kol Bo',
                 'Abudarham',
                 'Avodat HaKodesh',
                 'Machzor Vitry',
                 'Sefer Chasidim',
                 'Sefer HaParnas',
                 "Sheiltot d'Rav Achai Gaon",
                 ]

cat_other_a = create_category(["Halakhah", "Other Acharonim"], "Other Acharonim", "אחרונים נוספים")
books_other_a = ['Maaseh Rav',
                 'Nehar Misrayim',
                 'Shulchan Aruch HaRav',
                 ]

cat_shm = create_category(["Halakhah", "Sifrei Mitzvot", 'Sefer HaMitzvot'],'Sefer HaMitzvot','ספר המצוות')
moveIndexInto('Sefer HaMitzvot', cat_shm)

cat_shm_com = create_category(["Halakhah", "Sifrei Mitzvot", 'Sefer HaMitzvot', 'Commentary'])
on_sefer_hamitzvot = [
    "Hasagot HaRamban on Sefer HaMitzvot",
    "Kinaat Sofrim on Sefer HaMitzvot",
    "Lev Sameach",
    "Marganita Tava on Sefer HaMitzvot",
    "Megilat Esther on Sefer HaMitzvot",
]

for cat, books in [
    (cat_mono, books_mono),
    (cat_mitzvot, books_mitzvot),
    (cat_ivh, books_ivh),
    (cat_other_r, books_other_r),
    (cat_other_a, books_other_a),
    (cat_shm_com, on_sefer_hamitzvot)
]:
    for book in books:
        moveIndexInto(book, cat)

# Change 'Tur and Commentaries' -> 'Tur'
c = Category().load({"path": ["Halakhah", "Tur and Commentaries"]})
c.change_key_name("Tur")
c.save(override_dependencies=True)

tur_commentary = create_category(["Halakhah", "Tur", "Commentary"])

for ind in IndexSet({"categories": ["Halakhah", "Tur and Commentaries"]}):
    assert isinstance(ind, Index)
    ind.categories = ["Halakhah", "Tur"] if ind.get_title("en") == "Tur" else ["Halakhah", "Tur", "Commentary"]
    print("Moving - " + ind.get_title() + " to " + str(ind.categories))
    ind.save(override_dependencies=True)

# Move into Shulchan Arukh / Mishneh Torah subcats
moveIndexInto("Summary of Shakh on Shulchan Arukh, Yoreh De'ah",
              ["Halakhah", "Shulchan Arukh", "Commentary", "Siftei Kohen"])
moveIndexInto("Summary of Taz on Shulchan Arukh, Yoreh De'ah",
              ["Halakhah", "Shulchan Arukh", "Commentary", "Turei Zahav"])
moveIndexInto("Biur Halacha", ["Halakhah", "Shulchan Arukh", "Commentary", "Mishnah Berurah"])

# Move categories of Kesef Mishnah to correct place
new_parent = create_category(["Halakhah", "Mishneh Torah", "Commentary", "Kessef Mishneh"])
cs = CategorySet({"$and": [{"path.0": "Halakhah"}, {"path.1": "Commentary"}, {"path.2": "Kessef Mishneh"},
                           {"path.3": "Mishneh Torah"}]})
for c in cs:
    if len(c.path) == 4:
        continue
    moveCategoryInto(c, new_parent)


# Rosh: Fix leading space and missing "
for i in IndexSet({"schema.titles.text": {"$regex": "^ פסקי הראש"}}):
    new_title = i.get_title("he").replace(" פסקי הראש", 'פסקי הרא"ש')
    i.set_title(new_title, "he")
    i.save(override_dependencies=True)

# Musar
r_cat = create_category(["Musar", "Rishonim"], "Rishonim", "ראשונים")
a_cat = create_category(["Musar", "Acharonim"], "Acharonim", "אחרונים")
m_cat = create_category(["Musar", "Modern"], "Modern", "ספרות מודרנית")

r_books = [
    'Mivchar HaPeninim',
    'The Improvement of the Moral Qualities',
    'Shekel HaKodesh',
    'Letter from Ramban to his Son',
    'Shaarei Teshuvah',
    "Sha'ar Ha'Gemul of the Ramban",
    'Iggeret HaRamban',
    'Kad HaKemach',
    "Orchot Chaim L'HaRosh",
    'Sefer HaYashar',
    'Bechinat Olam',
    'Orchot Tzadikim',
    'Yesod HaYirah',
    'Sefer Tomer Devorah']

a_books = [
    'Kav HaYashar',
    'Shenei Luchot HaBerit',
    'Yaarot Devash I',
    'Shevet Musar',
    'Ahavat David',
    'Iggeret HaGra',
    'Messilat Yesharim',
    'Ohr Yisrael',
    'Pele Yoetz',
    'Shemirat HaLashon',
    "Yesod V'Shoresh HaAvodah",
    "Maamar Torat HaBayit"]

m_books = [
    "Tzipita L'Yeshuah",
    'Sichot Avodat Levi',
    'Shuvah Yisrael',
    'Maamar Mezake HaRabim'
]

for cat, books in [
    (r_cat, r_books),
    (a_cat, a_books),
    (m_cat, m_books)
]:
    for book in books:
        moveIndexInto(book, cat)

# Chassidut
moveIndexInto("Pri Tzadik", ["Chasidut", "R' Tzadok HaKohen"])
moveIndexInto("Mekor Mayim Chayim on Baal Shem Tov", ["Chasidut"])
moveIndexInto("Keter Shem Tov", ["Chasidut", "Early Works"])

c = create_category(["Chasidut", "Izhbitz"], "Izhbitz", "איזביצה")
for t in [
    "Tiferet Yosef",
    "Sod Yesharim",
    "Mei HaShiloach",
    "Beit Yaakov on Torah",
    "Shaar HaEmunah Ve'Yesod HaChassidut"
]:
    moveIndexInto(t, c)

c = create_category(["Chasidut", "Other Chasidut Works"], "Other Chasidut Works", "ספרי חסידות נוספים")
for t in [
    "Flames of Faith",
    "Agra DeKala",
    "Arvei Nachal",
    "Avodat Yisrael",
    "Baal Shem Tov",
    "Be'er Mayim Chaim",
    "Beit Aharon",
    "Bnei Yissaschar",
    "Chiddushei HaRim on Torah",
    "Chovat HaTalmidim",
    "Darkhei Yesharim",
    "Degel Machaneh Ephraim",
    "Derekh Mitsvotekha",
    "Divrei Emet",
    "Keter Shem Tov",
    "Maor VaShemesh",
    "Me'or Einayim",
    "Mekor Mayim Chayim on Baal Shem Tov",
    "Ohev Yisrael",
    "Sefat Emet",
    "Shem MiShmuel",
    "Shivchei HaBesht",
    "Tiferet Shlomo",
    "Yakar MiPaz",
    "Yismach Moshe",
    "Mareh Yechezkel on Torah"
]:
    moveIndexInto(t, c)


i = library.get_index("Be'er Mayim Chaim")
del i.dependence
del i.base_text_titles
i.save(override_dependencies=True)

# Kabbalah
c = create_category(["Kabbalah", "Zohar"], None, None)
for t in ["Zohar", "Tikkunei Zohar", "Zohar Chadash", "Baal HaSulam's Introduction to Zohar"]:
    moveIndexInto(t, c)

sy = create_category(["Kabbalah", "Sefer Yetzirah"], "Sefer Yetzirah", "ספר יצירה")
for t in ["Sefer Yetzirah", "Sefer Yetzirah Gra Version"]:
    moveIndexInto(t, sy)

syc = create_category(["Kabbalah", "Sefer Yetzirah", "Commentary"])
for t in ["HaGra on Sefer Yetzirah Gra Version",
          "Pri Yitzhak on Sefer Yetzirah Gra Version",
          "Ramban on Sefer Yetzirah",
          "Raavad on Sefer Yetzirah",
          "Rasag on Sefer Yetzirah"
          ]:
    moveIndexInto(t, syc)

c = create_category(["Kabbalah", "Ramchal"])
for t in ["Assarah Perakim L'Ramchal",
          "Da'at Tevunoth",
          "Kalach Pitchei Chokhmah",
          "Derech Etz Chayim (Ramchal)"]:
    moveIndexInto(t, c)

c = create_category(["Kabbalah", "Ramak"], "Ramak", 'רמ"ק')
for t in ["Or Neerav",
        "Pardes Rimonim"]:
    moveIndexInto(t, c)

c = create_category(["Kabbalah", "Arizal / Chaim Vital"], "Arizal / Chaim Vital", 'כתבי האר"י - חיים ויטאל')
for t in ["Pri Etz Chaim",
    "Sefer Etz Chaim",
    "Sha'ar HaGilgulim",
    "Shaarei Kedusha"]:
    moveIndexInto(t, c)

c = create_category(["Kabbalah", "Other Kabbalah Works"], "Other Kabbalah Works", "ספרי קבלה נוספים")
for t in [
    "Pri Etz Hadar",
    "The Beginning of Wisdom",
    "Avodat HaKodesh (Gabbai)",
    "Be'ur Eser S'firot",
    "Chesed LeAvraham",
    "Ma'arekhet HaElokut",
    "Maaseh Rokeach on Mishnah",
    "Maggid Meisharim",
    "Megaleh Amukot",
    "Mitpachat Sefarim",
    "Recanati on the Torah",
    "Sefer HaKana",
    "Shaarei Orah",
    "Shaarei Tzedek",
    "The Wars of God"
]:
    moveIndexInto(t, c)


# Responsa
rashba = {
    'Teshuvot haRashba part I': 1,
    'Teshuvot haRashba part IV': 4,
    'Teshuvot haRashba part V': 5,
    'Teshuvot haRashba part VI': 6,
    'Teshuvot haRashba part VII': 7,
    'Teshuvot haRashba Meyuchas LehaRamban': 10,
    'Footnotes to Teshuvot haRashba part IV': 14,
    'Footnotes to Teshuvot haRashba part V': 15,
    'Footnotes to Teshuvot haRashba part VI': 16,
    'Footnotes to Teshuvot haRashba part VII': 17,
}
for t, o in rashba.items():
    i = library.get_index(t)
    i.order = [o]
    i.save(override_dependencies=True)

moveIndexInto("Pe'er HaDor Teshuvot HaRambam", ["Responsa", "Rambam"])

cat_geonim = create_category(["Responsa", "Geonim"], "Geonim", "גאונים")
books_geonim = [
    'Epistle of Rav Sherira Gaon',
    "Musafia Teshuvot HaGeonim",
    'Teshuvot HaGeonim',
    'Toratan shel Rishonim'
]
cat_other_r = create_category(["Responsa", "Other Rishonim"], "Other Rishonim", "ראשונים נוספים")
books_other_r = [
    'Teshuvot Rashi',
    'Teshuvot HaRi Migash',
    'Teshuvot Maharam',
    'Maharach Or Zarua Responsa',
    'Teshuvot HaRitva',
    'Teshuvot HaRosh',
    'Teshuvot HaRivash',
    'Teshuvot Maharil',
    'Sefer HaTashbetz',
    'Mahari Weil',
    'Terumat HaDeshen',
    'Teshuvot HaRashbash',
    'Teshuvot Maharik',
    'Mahari Bruna'
]

cat_other_a = create_category(["Responsa", "Other Acharonim"], "Other Acharonim", "אחרונים נוספים")
books_other_a = [
    'Shut min haShamayim',
    'Chazeh Hatenufa',
    'Responsa of Remah',
    'Teshuvot Maharshal',
    'Responsa Maharashdam',
    'Teshuvot Maharit',
    'Havot Yair',
    'Hakham Tzvi',
    'Torat Netanel',
    'Noda BiYhudah I',
    'Noda BiYhudah II',
    'Teshuva MeAhava Part I',
    'Responsa Chatam Sofer',
    'Binyan Tziyon',
    'HaElef Lekha Shlomo',
    'Responsa Rav Pealim',
    'Mateh Levi',
    "Melamed Leho'il Part I",
    "Melamed Leho'il Part II",
    "Melamed Leho'il Part III",

]

cat_other_m = create_category(["Responsa", "Other Modern"], "Other Modern", "שו”תים מודרניים נוספים")
books_other_m = ['Responsa Benei Banim',
                 'LaKelal VeLaPerat',
                 'Mishpetei Uziel',
                 'Collected Responsa in Wartime',
                 'Collected Responsa to Chaplains']

for cat, books in [
    (cat_geonim, books_geonim),
    (cat_other_m, books_other_m),
    (cat_other_r, books_other_r),
    (cat_other_a, books_other_a)
]:
    for book in books:
        moveIndexInto(book, cat)

g = Group().load({"name": "Lindenbaum Center at YCT Rabbinical School"})
g.toc["categories"] = ["Responsa", "Other Modern"]
g.save(override_dependencies=True)

"""
Now an empty cat, because single text is hidden
i = library.get_index("Footnotes on Teshuvot haRashba Meyuchas LehaRamban"),
 currently: 
"categories": [
"Responsa",
"Commentary",
"Footnotes",
"Rashba"
],
"""

# Hide
tohide = [
    "Abraham Cohen Footnotes to the English Translation of Masechet Berakhot",
    "Footnotes on Teshuvot haRashba Meyuchas LehaRamban",
    "Footnotes on Orot",
    "Footnotes on Mekhilta DeRabbi Shimon Bar Yochai",
    "Footnotes to Kohelet by Bruce Heitler",
    "Footnotes to Teshuvot haRashba part IV",
    "Footnotes to Teshuvot haRashba part V",
    "Footnotes to Teshuvot haRashba part VI",
    "Footnotes to Teshuvot haRashba part VII",
    "Nishmat Adam",
    "Binat Adam",
    "Commentary on Selected Paragraphs of Arpilei Tohar",
    "Ali Be'er on Revealment and Concealment in Language",
    "Bein HaShitin on Halacha and Aggadah",
    "Commentaries on Revealment and Concealment in Language",
    "Publisher's Haggahot on Sefer HaParnas",
    "JPS 1985 Footnotes",
    "Notes and Corrections on Midrash Aggadah",
    "Buber footnotes on Midrash Mishlei",
    "Footnotes and Annotations on Derech Chaim",
    "Footnotes and Annotations on Be'er HaGolah",
    "Footnotes and Annotations on Ohr Chadash",
    "Footnotes and Annotations on Ner Mitzvah",
    "Footnotes and Annotations on Gevurot Hashem",
    "Footnotes and Annotations on Netivot Olam",

]
for t in tohide:
    i = library.get_index(t)
    i.hidden = True
    i.save(override_dependencies=True)

# Move Footnotes out of empty-display categories
moveIndexInto("Footnotes on Teshuvot haRashba Meyuchas LehaRamban", ["Responsa", "Rashba"])
moveIndexInto("JPS 1985 Footnotes", ["Tanakh", "Commentary"])
moveIndexInto("Footnotes on Orot", ["Jewish Thought"])
moveIndexInto("Footnotes on Mekhilta DeRabbi Shimon Bar Yochai", ["Midrash", "Halachic Midrash"])
moveIndexInto("Buber footnotes on Midrash Mishlei", ["Midrash", "Aggadic Midrash"])
moveIndexInto("Notes and Corrections on Midrash Aggadah", ["Midrash", "Aggadic Midrash"])
for t in ["Footnotes and Annotations on Be'er HaGolah",
    "Footnotes and Annotations on Ohr Chadash",
    "Footnotes and Annotations on Ner Mitzvah",
    "Footnotes and Annotations on Gevurot Hashem",
    "Footnotes and Annotations on Netivot Olam",]:
    moveIndexInto(t, ["Jewish Thought", "Maharal"])

##
c = Category().load({"path": ["Tanakh", "Commentary", "Imrei Yosher"]})

for t in [
    "Tzror HaMor on Song of Songs",
    "Palgei Mayim on Lamentations",
    "Megillat Setarim on Esther",
    "Ta'alumot Chokhmah on Ecclesiastes",
]:
    moveIndexInto(t, c)

library.rebuild(include_toc=True)

# Arrange Commentary on Tanakh
ri = ["Ralbag",
      "Ralbag Beur HaMilot",
      "Joseph ibn Yahya",
      "Abarbanel",
      "Alshich",
      "Saadia Gaon",
      "Second Version of Ibn Ezra",
      "Rosh on Torah",
      "Paaneach Raza",
      'Shelom Esther',
      "Rashi",
      "Immanuel of Rome on Esther",
      "Chizkuni",
      "Rabbeinu Bahya",
      "Rabbeinu Chananel",
      "Rashbam",
      "Tur HaAroch",
      "Baal HaTurim",
      "Bekhor Shor",
      "Daat Zkenim",
      "Ibn Ezra",
      "Kitzur Baal Haturim",
      "Radak",
      "Ramban",
      "Riva on Torah",
      "Toledot Yitzchak on Torah",
      "Minchat Shai",
      "Bartenura on Torah",
      'Sforno',
      'Tzror HaMor on Torah',
      "Mashmia Yeshuah",
      ]

ah = ["Avi Ezer",
      "Ba'alei Brit Avram",
      "Beit HaLevi on Torah",
      "Chanukat HaTorah",
      "Chatam Sofer on Torah",
      "Gur Aryeh",
      "HaKtav VeHaKabalah",
      "Haamek Davar",
      "Harchev Davar",
      "Imrei Yosher",
      "Kli Yakar",
      "Malbim",
      "Meshech Hochma",
      "Mizrachi",
      "Sepher Torat Elohim",
      "Shadal",
      "Tevat Gome",
      "Metzudat David",
      "Metzudat Zion",
      "Torah Temimah",
      "Ohev Ger",
      'Or HaChaim',
      'Siftei Chakhamim',
      'Aderet Eliyahu',
      'Yeriot Shlomo on Torah',
      'Minei Targuma on Torah',
      'Rav Hirsch on Torah',
      'Mechir Yayin on Esther',
      'Yesha Elohim on Esther',
      'Ohr Chadash',
      'Aderet Eliyahu (Rabbi Yosef Chaim)',
      "Tzafnat Pa'neach on Torah",
      ]

co = [
    'Birkat Asher on Torah',
    'Footnotes to Kohelet by Bruce Heitler',
    'Chibbah Yeteirah on Torah',
    'Depths of Yonah',
    'From David to Destruction',
    "JPS 1985 Footnotes"
]

chida = [
    'Nachal Kedumim on Torah',
    'Chomat Anakh',
    'Nachal Eshkol',
    'Tzaverei Shalal',
    'Rosh David',
    'Nachal Sorek',
]

rr_books = ['Redeeming Relevance; Deuteronomy',
      'Redeeming Relevance; Exodus',
      'Redeeming Relevance; Genesis',
      'Redeeming Relevance; Numbers'
]


moveCategoryInto(["Tanakh", "Commentary", "Malbim Beur Hamilot"], ["Tanakh", "Commentary", "Malbim"])

ri_cat = create_category(["Tanakh", "Rishonim on Tanakh"], "Rishonim on Tanakh", "ראשונים על התנ״ך")
ah_cat = create_category(["Tanakh", "Acharonim on Tanakh"], "Acharonim on Tanakh", "אחרונים על התנ״ך")
mo_cat = create_category(["Tanakh", "Modern Commentary on Tanakh"], "Modern Commentary on Tanakh",
                           "פירושים מודרניים על התנ״ך")
chida_cat = create_category(["Tanakh", "Acharonim on Tanakh", "Chida"], "Chida", 'חיד״א')
rr_cat = create_category(["Tanakh", "Modern Commentary on Tanakh", "Redeeming Relevance"], "Redeeming Relevance", "פדיון הרלוונטיות")

# Currently Tanakh, Commentary, <Index>
# or        Tanakh, Commentary, <subcat>, <Index>
groups = [
    (ri, ri_cat),
    (ah, ah_cat),
    (co, mo_cat),
    (chida, chida_cat),
    (rr_books, rr_cat)
]

for works, cat in groups:
    for n in works:
        cs = CategorySet({"path": ["Tanakh", "Commentary", n]})
        if cs.count():
            for c in cs:
                moveCategoryInto(c, cat)
        else:
            try:
                moveIndexInto(n, cat)
            except Exception:
                print("Can not figure out Tanakh Commnentary: {}".format(n))

moveIndexInto('Penei David', chida_cat)  # So that it doesn't move the category over.

g = Group().load({"name": "גיליונות נחמה"})
g.toc["categories"] = ["Tanakh", "Modern Commentary on Tanakh"]
g.save(override_dependencies=True)

###
### Mishnah Commentary

ri = [
    "Rashi",
    "Magen Avot",
    "Rambam",
    "Bartenura",
    "R' Shemaiah on Mishnah Middot",
    "Raavad on Mishnah Eduyot",
    "Rabbeinu Yonah",
    "Rash MiShantz",
]

ah = [
    "Yachin",
    "Boaz",
    "Derech Chaim",
    "Gra",
    "Hon Ashir",
    "Midrash Shmuel on Avot",
    "Nachalat Avot on Avot",
    "Yein Levanon on Avot",
    "Zeroa Yamin",
    "Ikar Tosafot Yom Tov",
    "Tosafot Yom Tov",
    "Tosafot Rabbi Akiva Eiger",
    "Melechet Shlomo",
    "Lechem Shamayim",
    "Marit HaAyin",
    "Petach Einayim",
    "Rashash",
    "Yesh Seder LaMishnah",
]

co = [
    "English Explanation of Mishnah",
    "A New Israeli Commentary on Pirkei Avot",
    "Footnotes and Annotations on Derech Chaim",
]

ri_cat = create_category(["Mishnah", "Rishonim on Mishnah"], "Rishonim on Mishnah", "ראשונים על המשנה")
ah_cat = create_category(["Mishnah", "Acharonim on Mishnah"], "Acharonim on Mishnah", "אחרונים על המשנה")
mo_cat = create_category(["Mishnah", "Modern Commentary on Mishnah"], "Modern Commentary on Mishnah",
                           "פירושים מודרניים על המשנה")

groups = [
    (ri, ri_cat),
    (ah, ah_cat),
    (co, mo_cat),
]

for works, cat in groups:
    for n in works:
        cs = CategorySet({"path": ["Mishnah", "Commentary", n]})
        if cs.count():
            for c in cs:
                moveCategoryInto(c, cat)
        else:
            try:
                moveIndexInto(n, cat)
            except Exception:
                print("Can not figure out Mishnah Commnentary: {}".format(n))

moveIndexInto("Motar Kinnim", ah_cat) # Don't want to move the category -  deleted below.

####
#### Talmud Commentary


ri = ['Rashi',
      'Tosafot',
      'Rif',
      'Rashba',
      "Chidushei HaRa'ah on Berakhot",
      'Tosafot Chad Mikamei on Yevamot',
      'Yad Ramah on Bava Batra',
      'Chidushei HaMeiri',
      'Commentary of the Rosh',
      'Ktav Yad Rashi',
      'Mefaresh on Tamid',
      'Mordechai',
      'Rabbeinu Chananel',
      'Rabbeinu Gershom',
      'Ramban',
      'Ran',
      'Rashbam',
      'Rav Nissim Gaon',
      'Ritva',
      'Rosh',
      'Tosafot HaRosh',
      'Tosafot Ri HaZaken',
      'Tosafot Rid',
      'Tosafot Shantz',
      'Tosafot Yeshanim',
      'Yad Ramah']

ah = ['Haflaah on Ketubot',
      'Ben Yehoyada',
      'Benayahu',
      'Chiddushei Rabbi Akiva Eiger',
      'Chidushei Agadot',
      'Chidushei Chatam Sofer',
      'Chidushei Halachot',
      'Chokhmat Shlomo',
      'Ein Ayah',
      'Maharam',
      'Maharam Shif',
      'Marit HaAyin',
      'Penei Yehoshua',
      'Petach Einayim',
      'Shita Mekubetzet',
      'Rashash'
]

co = ['Beur Reuven on Bava Kamma',
      'Reshimot Shiurim',
      'Steinsaltz',
      'Daf Shevui',
      "Abraham Cohen Footnotes to the English Translation of Masechet Berakhot"]

rc = [
    'Korban Netanel',
    'Maadaney Yom Tov',
    'Pilpula Charifta',
    'Tiferet Shmuel',
    'Divrey Chamudot',
]


ri_cat = create_category(["Talmud", "Bavli", "Rishonim on Talmud"], "Rishonim on Talmud", "ראשונים על התלמוד")
ah_cat = create_category(["Talmud", "Bavli", "Acharonim on Talmud"], "Acharonim on Talmud", "אחרונים על התלמוד")
mo_cat = create_category(["Talmud", "Bavli", "Modern Commentary on Talmud"], "Modern Commentary on Talmud",
                           "פירושים מודרניים על התלמוד")
rc_cat = create_category(["Talmud", "Bavli", "Rishonim on Talmud", "Rosh", "Commentary"])

groups = [
    (ri, ri_cat),
    (ah, ah_cat),
    (co, mo_cat),
    (rc, rc_cat)
]

for works, cat in groups:
    for n in works:
        cs = CategorySet({"path": ["Talmud", "Bavli", "Commentary", n]})
        if cs.count():
            for c in cs:
                moveCategoryInto(c, cat)
        else:
            try:
                moveIndexInto(n, cat)
            except Exception:
                print("Can not figure out ￿Talmud Commnentary: {}".format(n))

for p in [
    ["Halakhah", "Mishneh Torah"],
    ["Halakhah", "Shulchan Arukh"],
    ["Halakhah", "Tur"],
    ["Kabbalah", "Sefer Yetzirah"],
    ["Jewish Thought", "Rishonim", "Duties of the Heart"]
]:
    c = Category().load({"path": p})
    c.isPrimary = True
    c.save(override_dependencies=True)

library.rebuild(include_toc=True)

moveIndexInto('Yad Ramah on Bava Batra', ["Talmud", "Bavli", "Rishonim on Talmud", "Yad Ramah"])

###


for p in [
    ["Other", "Grammar"],
    ["Other", "Dictionary"],
    ["Modern Works", "Commentary"],
    ["Tanaitic", "Commentary"],
    ["Responsa", "Commentary", "Footnotes", "Rashba"],
    ["Jewish Thought", "Commentary", "Footnotes"],
    ["Midrash", "Commentary", "Footnotes", "Halachic Midrash"],
    ["Midrash", "Commentary", "Buber footnotes", "Aggadic Midrash"],  # Merely hidden
    ["Midrash", "Commentary", "Gra", "Aggadic Midrash"],  # empty
    ["Midrash", "Commentary", "Meir Ayin", "Aggadic Midrash"],  # empty
    ["Midrash", "Commentary", "Yaakov Emden", "Aggadic Midrash"],  # empty
    ["Tanakh", "Commentary", "Palgei Mayim"],
    ["Tanakh", "Commentary", "Megillat Setarim"],
    ["Tanakh", "Commentary", "Ta'alumot Chokhmah"],
    ["Mishnah", "Commentary", "R' Shemaiah"],
    ["Mishnah", "Commentary", "Raavad"],
    ["Mishnah", "Commentary", "Motar Kinnim", "Seder Kodashim"],
    ["Talmud", "Bavli", "Commentary", "Ri HaZaken", "Seder Nashim"],
    ["Jewish Thought", "Maharal", "Commentary"],
    ["Halakhah", "Commentary", "Shulchan Arukh"],
    ["Halakhah", "Commentary", "Summary of Taz", "Shulchan Arukh"],
    ["Halakhah", "Commentary", "Summary of Shakh", "Shulchan Arukh"],
    ["Kabbalah", "Commentary", "Gra"],
    ["Kabbalah", "Commentary", "Pri Yitzhak"],
    ["Kabbalah", "Commentary", "Ramban"],
    ["Kabbalah", "Commentary", "Raavad"],
    ["Kabbalah", "Commentary", "Saadia Gaon"],
    ["Jewish Thought", "Commentary", "Marpeh la'Nefesh", "Duties of the Heart"],
    ["Jewish Thought", "Commentary", "Pat Lechem", "Duties of the Heart"],
    ["Jewish Thought", "Commentary", "Tov haLevanon", "Duties of the Heart"],
    ["Tanakh", "Commentary", "Penei David"],
    ["Talmud", "Bavli", "Commentary", "Mefaresh", "Seder Kodashim"],
]:
    c = Category().load({"path": p})
    if c:
        c.delete(override_dependencies=True)
    else:
        print("Failed to load category for {}".format(p))

library.rebuild(include_toc=True)
for p in [
    ["Halakhah", "Commentary", "Kessef Mishneh", "Mishneh Torah"],
    ["Other"],
    ["Modern Works"],
    ["Tanaitic"],
    ["Responsa", "Commentary", "Footnotes"],
    ["Midrash", "Commentary", "Footnotes"],
    ["Tanakh", "Commentary", "JPS"],
    ["Tanakh", "Commentary", "Bartenura"],
    ["Midrash", "Commentary", "Buber footnotes"],
    ["Midrash", "Commentary", "Gra"],
    ["Midrash", "Commentary", "Meir Ayin"],
    ["Midrash", "Commentary", "Yaakov Emden"],
    ["Midrash", "Commentary", "Notes and Corrections on Midrash Aggadah"],
    ["Tanakh", "Commentary", "Riva"],
    ["Chasidut", "Commentary"],
    ["Mishnah", "Commentary", "Motar Kinnim"],
    ["Mishnah", "Commentary", "Seder Nezikin"],
    ["Talmud", "Bavli", "Commentary", "Ri HaZaken"],
    ["Talmud", "Bavli", "Commentary", "Mefaresh"],
    ["Halakhah", "Commentary", "Summary of Taz"],
    ["Halakhah", "Commentary", "Summary of Shakh"],
    ["Kabbalah", "Commentary"]
]:
    c = Category().load({"path": p})
    if c:
        c.delete(override_dependencies=True)
    else:
        print("Failed to load category for {}".format(p))

library.rebuild(include_toc=True)
for p in [
    ["Halakhah", "Commentary", "Kessef Mishneh"],
    ["Responsa", "Commentary"],
    ["Tanakh", "Commentary"],
    ["Talmud", "Bavli", "Commentary"],
    ["Mishnah", "Commentary"],
    ["Midrash", "Commentary"],

]:
    c = Category().load({"path": p})
    if c:
        c.delete(override_dependencies=True)
    else:
        print("Failed to load category for {}".format(p))


library.rebuild(include_toc=True)

#Check if any categories are using titles when they could use terms
cs = CategorySet({"sharedTitle": None})
for c in cs:
    t = Term().load({"name": c.get_primary_title()})
    if t:
        c.add_shared_term(c.get_primary_title())
        # del c.titles
        c.save(override_dependencies=True)
    else:
        print("Category without term: {}".format(c.get_primary_title()))

# Category without term: Motar Kinnim
# Category without term: Eliezer Berkovits

#	Alphabetical  (? really?  not crono?)
# Click Talmud -> Commentary of Chida (crash)
