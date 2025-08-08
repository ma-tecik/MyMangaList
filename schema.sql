create table authors
(
    id     INTEGER
        primary key autoincrement,
    id_mu  TEXT
        unique,
    id_dex TEXT
        unique,
    id_mal INTEGER
        unique,
    name   TEXT
);

create table authors_names
(
    id   INTEGER not null
        references authors
            on delete cascade,
    name TEXT    not null,
    unique (id, name)
);

create table genres
(
    id    INTEGER
        primary key autoincrement,
    genre TEXT not null
        unique
);

create table nhentai_ids
(
    nhentai_id INTEGER not null
        primary key
);

create table schale_ids
(
    schale_id  INTEGER not null
        primary key,
    schale_key TEXT    not null
);

create table series
(
    id           INTEGER
        primary key autoincrement,
    id_mu        TEXT
        unique,
    id_dex       TEXT
        unique,
    id_bato      INTEGER
        unique,
    id_mal       INTEGER
        unique,
    id_line      INTEGER
        unique,
    title        TEXT not null,
    type         TEXT not null,
    description  TEXT,
    vol_ch       TEXT,
    year         INTEGER,
    timestamp_mu INTEGER,
    is_md        BOOLEAN default 0,
    status       TEXT not null,
    user_rating  REAL
        check (status in ('Plan to Read', 'Reading', 'Completed', 'One-shot', 'Dropped', 'Ongoing'))
);

create table series_titles
(
    id        INTEGER
        primary key autoincrement,
    series_id INTEGER not null
        references series
            on delete cascade,
    alt_title TEXT    not null,
    unique (series_id, alt_title)
);

create index idx_alt_titles_series_id
    on series_titles (series_id);

create table series_authors
(
    series_id   INTEGER               not null
        references series
            on delete cascade,
    author_id   INTEGER               not null
        references authors
            on delete cascade,
    author_type TEXT default 'Author' not null,
    primary key (series_id, author_id, author_type),
    check (author_type IN ('Author', 'Artist', 'Both'))
);

create index series_authors_series_id
    on series_authors (series_id);

create table series_genres
(
    series_id INTEGER not null
        references series
            on delete cascade,
    genre_id  INTEGER not null
        references genres
            on delete cascade,
    primary key (series_id, genre_id)
);

create index series_genres_series_id
    on series_genres (series_id);

create table series_images
(
    extension TEXT    not null,
    series_id integer not null
        primary key
        references series
            on delete cascade
);

create table series_nhentai_ids
(
    series_id  INTEGER not null
        references series
            on delete cascade,
    nhentai_id INTEGER not null
        references nhentai_ids
            on delete cascade,
    primary key (series_id, nhentai_id)
);

create table series_ratings_mu
(
    id_mu  INTEGER not null
        primary key
        references series (id_mu)
            on delete cascade,
    rating REAL    not null,
    votes  INTEGER not null
);

create index idx_series_ratings_rating
    on series_ratings_mu (rating);

create table series_schale_ids
(
    series_id INTEGER not null
        references series
            on delete cascade,
    schale_id INTEGER not null
        references schale_ids
            on delete cascade,
    primary key (series_id, schale_id)
);

create table settings
(
    key   TEXT not null
        primary key,
    value TEXT not null
);