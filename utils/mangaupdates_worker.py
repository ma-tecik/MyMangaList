def worker(genres, data):
    valid_categories = [entry.get("category") for entry in data if
                        entry.get("votes_minus", 0) <= entry.get("votes_plus", 0)]
    genre_map = {
        "Os Coll.": ["Anthology", "Collection of Stories", "Oneshot", "Promotional Oneshot", "Short Story",
                       "Promotional Short Series"],
        "Cancelled": ["Axed/Cancelled/Discontinued", "Incomplete Due to Author/Artist Death"],
        "Rushed": ["Rushed Ending / Not Axed"],
        "Webtoon": ["Full Color", "Manga with Webtoon Version", "Webtoon"],
        "Old-Style": ["Old-Style Drawings"],
        "Award": ["Award-Winning Work", "Award-Nominated Work"],
        "European": [
            "Commoner to Noble", "Corrupt Royal Member/s", "Crown Prince/s", "Former Royalty",
            "Hidden Noble Status", "King/s", "Kingdom/s", "Nobility/Aristocracy",
            "Noble Female Lead", "Noble Girl", "Noble Male Lead", "Noble Protagonist",
            "Noble to Commoner", "Noble-Commoner Relationship", "Politics Involving Royalty",
            "Prince Male Lead", "Prince-Commoner Relationship", "Prince/s",
            "Prince/ss-Commoner Relationship", "Princess Female Lead", "Princess/es",
            "Queen Female Lead", "Queen/s", "Royal Court", "Royal-Commoner Relationship",
            "Royal-Knight Relationship", "Royal-Noble Relationship", "Royalty"
        ],
        "European_real": ["European Ambience", "Medieval European Ambience"],
        "Asian": [
            "Ancient China", "Ancient Japan", "Ancient Korea", "Asian Theme", "Chinese Ambience",
            "East Asian Ambience", "Edo Period", "Feudal Japan", "Ieyasu Tokugawa or a Relative",
            "Heian Era", "Heisei Era", "Japanese Ambience", "Japanese Imperialism", "Jishou Era",
            "Joseon Era", "Kamakura Period", "Keio Era", "Korea Under Japanese Rule",
            "Korean Ambience", "Korean Folklore", "Meiji Era", "Muromachi Period",
            "Nobunaga or a Relative", "Oiran", "Reiwa Era", "Sengoku Era", "Showa Era",
            "Taisho Era", "Three Kingdoms Period", "Yoshiwara District"
        ],
        "isekai": [
            "Author Transmigrated to Own Creation", "Isekai",
            "Multiple Persons From Another World", "Multiple Transmigrated Individuals",
            "Otome Isekai", "Reincarnation", "Reincarnated in a Book World",
            "Reincarnated in a Game World", "Reincarnated in Another World",
            "Summoned to Another World", "Time Transmigrating", "Transmigration",
            "Transmigrated as a Side/Mob Character", "Transmigrated as the Protagonist",
            "Transmigrated as the Villain/ess", "Transmigrated into a Book World",
            "Transmigrated into a Game", "Transmigrated into a Parallel World",
            "Transmigrated into an Otome Game", "Transmigrated into Ancient Era",
            "Transmigrated into Another World", "Transmigrated into Opposite Gender",
            "Transmigrated into Person with Death Fate", "Transmigrated into the Past",
            "Transported to Another World", "Transported to a Book World",
            "Transported to a Game World", "Transported to a Parallel World"
        ],
        "Reverse Isekai": ["Reverse Isekai"],
        "Time Rewind": ["Time Rewind"],
        "Villainess": [
            "Reincarnated as the Villain/ess", "Transmigrated as the Villain/ess",
            "Villain Couple", "Villain Protagonist", "Villain/s", "Villainess/es"
        ],
        "Revenge": ["Revenge"],
        "Modern": [
            "2000s", "2010s", "2020s", "21st Century", "Modern Era", "Modern City", "Modern Technology"
        ],
        "Childhood F.": ["Childhood Friends Become Lovers"],
        "Con. Marr.": ["Contract Marriage", "Contractual Relationship"],
        "Arranged Marr.": ["Arranged Marriage", "Arranged Relationship"],
        "Sensei": ["Student-Teacher Relationship", "School Nurse-Student Relationship", "Student-School Doctor Relationship"],
        "Age Gap": ["Age Gap"],
        "Office": ["Office Life", "Office Romance", "Office Worker/s", "Workplace Intercourse", "Workplace Romance"],
        "Boss-Sub": ["Boss", "Boss-Subordinate Relationship", "CEO/s", "Company President"],
        "Showbiz": ["Showbiz", "Acting", "Actor/s", "TV Show/s", "Idol/s", "Entertainment Industry",
                    "Celebrity/ies", "Actress/es", "Child Actor/Actress"],
        "inc.": ["Brother-Sister Incest", "False Incest", "Incest", "Incest-Like Relationship",
                 "Stepbrother-Stepsister Intercourse", "Stepsibling Love"],
        "Borderline H": ["Borderline H"],
        "Yandere": ["Yandere", "Yandere Male Lead"],
        "Toxic Rel.": ["Toxic Male Lead", "Toxic Relationship", "Trashy Male Lead"],
    }
    if "School Life" not in genres:
        genre_map["School Life"] = [
            "All-Boys School", "All-Girls School", "Boarding School", "Elite School",
            "High School", "Middle School", "Prestigious School", "Private School", "School",
            "School Club/s", "University/College"
        ]

    for genre, categories in genre_map.items():
        if any(entry in categories for entry in valid_categories):
            genres.append(genre)

    # Special case
    if "Asian" in genres and "European" in genres and "European_real" not in genres:
        genres.remove("European")
    if "European_real" in genres:
        if "European" not in genres:
            genres.append("European")
    if "European_real" in genres:
        genres.remove("European_real")

    return genres