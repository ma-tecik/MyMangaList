from flask import current_app as app
from typing import List

def base36(num: int) -> str:
    alphabet = '0123456789abcdefghijklmnopqrstuvwxyz'
    result = ''
    if 0 <= num < 36:
        return alphabet[num]
    while num > 0:
        num, i = divmod(num, 36)
        result = alphabet[i] + result
    return result

def author_type_merger(authors: List[dict]) -> List[dict]:
    merged_authors = {}
    if any(a.get("id_mu") or a.get("id_dex") or a.get("id_mal") for a in authors):
        for author in authors:
            author_id = author.get("id_mu") or author.get("id_dex") or author.get("id_mal")
            if author_id in merged_authors:
                merged_authors[author_id]['type'] = 'Both'
            else:
                merged_authors[author_id] = author
    else:
        for author in authors:
            name = author['name']
            type_ = author['type'].capitalize()
            if name not in merged_authors:
                merged_authors[name] = {'name': name, 'type': type_}
            else:
                merged_authors[name]['type'] = 'Both'
    return list(merged_authors.values())

def author_id_merger(authors: List[dict], series_data) -> List[dict]:
    merged_authors = []
    type_groups = {
        'Both': [a for a in authors if a.get('type') == 'Both'],
        'Author': [a for a in authors if a.get('type') == 'Author'],
        'Artist': [a for a in authors if a.get('type') == 'Artist']
    }
    for author_type, author_list in type_groups.items():
        if len(author_list) in (2, 3):
            id_type_values = {}
            for a in author_list:
                for k, v in a.items():
                    if k.startswith('id_'):
                        if k in id_type_values and id_type_values[k] != v:
                            app.logger.warning(f"Conflict in author_id_merge. Series:{series_data} Authors:{authors}")
                            return authors
                        id_type_values[k] = v
            merged_author = {'type': author_type}
            merged_author.update(id_type_values)
            merged_authors.append(merged_author)
        else:
            merged_authors.extend(author_list)
    return merged_authors

if __name__ == '__main__':
    pass