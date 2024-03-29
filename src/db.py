from supabase import create_client, Client
import traceback

def get_db_connection(url: str, key: str) -> Client:
    client = create_client(url, key)
    return client

def add_stats_to_db(client: Client, stats_list: list[dict]) -> None:
    try:
        data, count = client.table('prices').insert(stats_list).execute()
    except Exception:
        print(traceback.format_exc())