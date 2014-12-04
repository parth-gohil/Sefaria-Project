from sefaria.texts import *

merge_text_versions_by_language("Aruch HaShulchan", "he", warn=True)
merge_text_versions("Wikisource", "WikiSource", "Aruch HaShulchan", "en", warn=True)

merge_text_versions_by_source("Bereishit Rabbah", "he", warn=True)
merge_text_versions_by_source("Bereishit Rabbah", "en", warn=True)
merge_text_versions("Wikisource Bereshit Rabbah", "wikisource", "Bereishit Rabbah", "he", warn=True)

merge_text_versions_by_source("Mishnah Berurah", "he", warn=True)
merge_multiple_text_versions(["Hilchos Krias Shemah and Tefillos Maariv", "Mishnah Berurah: Siman 494", "Hilchos Shabbos #1", " Mishnah Berurah 494 Tfilot on Shavuot", "Mishnah Berurah 494 Tfilot on Shavuot"], "Mishnah Berurah", "he", warn=True)
update_version_title("Hilchos Krias Shemah and Tefillos Maariv", "Mishnah Berurah from OnYourWay", "Mishnah Berurah", "he")
merge_text_versions("eu5 text", "Halachos for Donning Clothing", "Mishnah Berurah", "he", warn=True)
merge_text_versions("Wikitext", "Wiki text", "Mishnah Berurah", "he", warn=True)
