from supabase import Client

class QueryContext():
    def __init__(self, id: int, query_terms: list[str], exclude_terms: list[str]) -> None:
        self.id = id
        self.query_terms = query_terms
        self.exclude_terms = exclude_terms

def get_query_context_list(client: Client) -> list[QueryContext]:
    context_list = []
    query_strings = client.table('queries').select('*').execute().data
    if len(query_strings) == 0:
        print("No query strings in DB yet!")
        return
    for query in query_strings:
        id = query.get('id')
        query_terms = query.get('query_string', '').split(' ')
        exclude_terms = query.get('exclude_string', '').split(' ')
        context_list.append(QueryContext(id, query_terms, exclude_terms))
    return context_list