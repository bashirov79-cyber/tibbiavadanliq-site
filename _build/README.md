# tibbiavadanliq.az — generator
- data.json: saytın bütün məlumatı (məhsullar, bölmələr, müəssisə səhifələri, axtarış sinonimləri `kw`).
- Yeniləmə (repo kökündən): python3 _build/build_ta.py . _build/data.json tibbiavadanliq.az agizgenislendirici changes.json
- changes.json formatı build_ta.py-nin başındadır (upsert / remove / images; 128px miniatür avtomatik yaranır).
- Dəyişiklik olmadan işə salsan, sayt hərfi-hərfinə eyni qalır.
- Silinən səhifələrin yolunu .deploy-remove.txt-ə yaz (serverdən də silinsin).
- Dərc: push → cPanel › Git Version Control › Manage › Pull or Deploy › Update from Remote → Deploy HEAD Commit.
