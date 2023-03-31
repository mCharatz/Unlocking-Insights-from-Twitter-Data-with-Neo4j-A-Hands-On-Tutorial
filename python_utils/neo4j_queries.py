import py2neo
import pandas as pd

port = input("Enter Neo4j DB Bolt port: ")
user = input("Enter Neo4j DB Username: ")
pswd = input("Enter Neo4j DB Password: ")
#graph = Graph("bolt://localhost:7687", auth=("neo4j", "neo4j_auth")

graph = py2neo.Graph(port, auth=(user, pswd))


#Get the total number of retweets
query1 = "MATCH p=()-[r:RETWEETED]->() RETURN COUNT(*)"
retweets = graph.run(query1).evaluate()
print("The total number of retweets is:", retweets)


#Get the 20 most popular hashtags (case insensitive) in descending order
query2 = """
    MATCH p=()-[r:HAS_HASHTAG]->(n:Hashtag)
    RETURN n.tag, COUNT(*) AS indegree
    ORDER BY indegree DESC
    LIMIT 20
"""
pop_hashtags = graph.run(query2)
print('hashtag, frequency')
for h in pop_hashtags:
    print(h['n.tag'], h['indegree'])


#Get the total number of URLs (unique)
query3 = "MATCH (n:URL) RETURN COUNT(n)"
urls = graph.run(query3).evaluate()
print("The total number of urls is:", urls)


#Get the 20 users with most followers in descending order
query4 = """
    MATCH (n:User)
    WHERE n.followers IS NOT NULL
    RETURN n.username, n.followers AS followers
    ORDER BY followers DESC
    LIMIT 20
"""
pop_users = graph.run(query4)
print('username, number of followers')
for u in pop_users:
    print(u['n.username'], u['followers'])


#Get the 20 users, in descending order, that have been mentioned the most
query6 = """
    MATCH p=()-[r:MENTIONED]->(n:User)
    RETURN n.username, COUNT(*) AS indegree
    ORDER BY indegree DESC
    LIMIT 20
"""
most_mentioned_users = graph.run(query6)
print('username, number of mentions')
for m in most_mentioned_users:
    print(m['n.username'], m['indegree'])


'''Get the top 20 tweets that has been retweeted the most and the persons that
posted them'''
query7 = """
    MATCH (n:Tweet)
    RETURN n.id, n.author, n.retweets as retweets
    ORDER BY retweets DESC
    LIMIT 20
"""
most_retweeted = graph.run(query7)
result_tweet_ids, result_tweet_author_id, result_tweet_num_retweets = [], [], []

for r in most_retweeted:
    result_tweet_ids.append(r['n.id'])
    result_tweet_author_id.append(r['n.author'])
    result_tweet_num_retweets.append(r['retweets'])

df = pd.DataFrame(list(zip(result_tweet_ids, result_tweet_author_id, result_tweet_num_retweets)),
               columns =['tweet_id', 'author_id', 'num_retweets'])

print(df)


'''Get the 10 users with most similar hashtags to 
the 4th important user(as the others used no hashtags)'''

def jaccard_sim(list1, list2):
    '''compute Jaccard similarity of two sets'''
    intersec = len(set(list1).intersection(set(list2)))
    union = len(set(list1).union(set(list2)))
    if union>0:
        return intersec / union
    else:
        return 0


def get_hashtags(name):
    '''get the hashtags used by 4th important user
    '''

    query = """
        MATCH (u:User)-[r:USED_HASHTAG]->(h:Hashtag)
        WHERE u.username = $name
        RETURN DISTINCT h.tag 
    """
    tags = graph.run(query,name = name)
    hashtags = [t["h.tag"] for t in tags]

    return hashtags


def get_most_similar_user(name):
    '''get the 10 users with most similar hashtags
    to the 4th important user'''

    user_tags = get_hashtags(name)
    query = '''MATCH (u:User)-[r:USED_HASHTAG]->(h:Hashtag)
    WHERE u.username <> $name
    RETURN u.username, COLLECT(h.tag) AS hashtags'''
    result = graph.run(query, name=name)
    tag_sim,  users = list(), list()
    for r in result:
        other_user = r["u.username"]
        other_tags = r["hashtags"]
        if len(other_tags)>0:
            sim= jaccard_sim(user_tags, other_tags)
            tag_sim.append(sim)
            users.append(other_user)
    tag_sim, users = zip(*sorted(zip(tag_sim, users)))
        
    sim_user = users[-20:]
    print(sim_user)


get_most_similar_user('WomensVoicesNow')