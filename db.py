from supabase import create_client, Client

def get_db_connection(url, key) -> Client:
    client = create_client(url, key)
    return client