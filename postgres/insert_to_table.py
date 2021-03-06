__author__ = 'snownettle'

import postgres_configuration
from da_taxonomy import dialogue_acts_taxonomy, matching_schema
from mongoDB import mongoDBQueries, mongoDB_configuration
from general import check_lang
from postgres_configuration import  fullOntologyTable, reducedOntologyTable, minimalOntologyTable
from postgres_queries import find_da_by_name, find_tweet_by_id


def insert_into_edit_tweet_table(conversation_list, connection, cursor):
    collection = mongoDB_configuration.get_collection(mongoDB_configuration.db_name,
                                                      mongoDB_configuration.collectionNameAllAnnotations)
    conversation_id = 1
    for conversation in conversation_list:
        all_tweets = conversation.all_nodes()
        for tweet in all_tweets:
            tweet_data = mongoDBQueries.find_by_id(collection, tweet.tag)[0]
            tweet_id = tweet_data['tweet_id']
            if tweet_data['text_id'] == 0:
                parent_tweet = 'NULL'
            else:
                parent_tweet = conversation.parent(tweet_id).tag
            tweet_text = tweet_data['text'].split('user=')[1]
            username = tweet_text.split(' ')[0]

            if tweet_text != '':

                tweet_text = tweet_text.split(username)[1]
                if '\'' in tweet_text:
                    tweet_text = tweet_text.replace('\'', '\'\'')
                german = check_lang.check_german(tweet_text)
                query = "INSERT INTO Tweet (Tweet_id, In_replay_to, Conversation_id, Tweet_text, German) " \
                    "VALUES (%s, %s, %s, \'%s\', %s) " % (tweet_id, parent_tweet, conversation_id, tweet_text, german)
                cursor.execute(query)
                connection.commit()
        conversation_id += 1


def insert_missing_tweet(tweet, previous_tweet,  cursor, connection):
    parent_tweet_id = previous_tweet.get_tweet_id()
    previous_tweet_db = find_tweet_by_id(parent_tweet_id, cursor)
    conversation_number = previous_tweet_db[3]
    tweet_id = tweet.get_tweet_id()
    tweet_text = tweet.get_text()
    if '\'' in tweet_text:
        tweet_text = tweet_text.replace('\'', '\'\'')
    german = check_lang.check_german(tweet_text)
    query = "INSERT INTO Tweet (Tweet_id, In_replay_to, Conversation_id, Tweet_text, German) " \
            "VALUES (%s, %s, %s, \'%s\', %s) " % (tweet_id, parent_tweet_id, conversation_number,
                                                  tweet_text, german)
    cursor.execute(query)
    connection.commit()


def insert_dialogue_act_names_full(connection, cursor):
    if select_da('Dialogue_act_full'):
        dialogue_act_names_tree = dialogue_acts_taxonomy.build_da_taxonomy_full()
        root = dialogue_act_names_tree.root
        da_list = list()
        da_tuple = (1, root, None)
        da_list.append(da_tuple)
        da_tuple = find_children(dialogue_act_names_tree, root, da_list)
        query = "INSERT INTO Dialogue_act_full (Dialogue_act_id, Dialogue_act_name, Parent_act_id) VALUES (%s, %s, %s)"
        cursor.executemany(query, da_tuple)
        connection.commit()


def insert_dialogue_act_names_reduced(connection, cursor):
    if select_da('Dialogue_act_reduced'):
        dialogue_act_names_tree = dialogue_acts_taxonomy.build_da_taxonomy_reduced()
        root = dialogue_act_names_tree.root
        da_list = list()
        da_tuple = (1, root, None)
        da_list.append(da_tuple)
        da_tuple = find_children(dialogue_act_names_tree, root, da_list)
        query = "INSERT INTO Dialogue_act_reduced (Dialogue_act_id, Dialogue_act_name, Parent_act_id) " \
                "VALUES (%s, %s, %s)"
        cursor.executemany(query, da_tuple)
        connection.commit()


def insert_dialogue_act_names_minimal(connection, cursor):
    if select_da('Dialogue_act_minimal'):
        dialogue_act_names_tree = dialogue_acts_taxonomy.build_da_taxonomy_minimal()
        root = dialogue_act_names_tree.root
        da_list = list()
        da_tuple = (1, root, None)
        da_list.append(da_tuple)
        da_tuple = find_children(dialogue_act_names_tree, root, da_list)
        query = "INSERT INTO Dialogue_act_minimal (Dialogue_act_id, Dialogue_act_name, Parent_act_id) " \
                "VALUES (%s, %s, %s)"
        cursor.executemany(query, da_tuple)
        connection.commit()


def find_children(tree, parent, da_list):
    if parent == 'DIT++ Taxonomy':
        children = tree.children(parent)
    else:
        children = tree.children(parent.tag)
    for child in children:
        if parent == 'DIT++ Taxonomy':
            current_tuple = (len(da_list) + 1, child.tag, 1)
        else:
            parent_id = find_parent_id(da_list, parent.tag)
            current_tuple = (len(da_list) + 1, child.tag, parent_id)
        da_list.append(current_tuple)
        find_children(tree, child, da_list)
    return da_list


def find_parent_id(da_list, parent_name):
    for da in da_list:
        if da[1] == parent_name:
            return da[0]
    return 0


def select_all_tweets():
    connection, cursor = postgres_configuration.make_connection()
    query = 'SELECT Tweet_id FROM Tweet'
    cursor.execute(query)
    results = cursor.fetchall()
    postgres_configuration.close_connection(connection)
    tweets_list = set()
    for result in results:
        tweets_list.add(str(result[0]))
    return tweets_list


def select_da(table):
    connection, cursor = postgres_configuration.make_connection()
    query = 'select * from ' + table
    cursor.execute(query)
    results = cursor.fetchall()
    if len(results) == 0:
        postgres_configuration.close_connection(connection)
        return True
    else:
        postgres_configuration.close_connection(connection)
        return False


def make_utterance(token_list, tweet_id, start_offset, end_offset):
    tweet = list()
    for i in range(0, len(token_list), 1):
        if token_list[i]['tweet_id'] == tweet_id:
            tweet.append(token_list[i])
    utterance = str()
    for i in range(start_offset, end_offset+1, 1):
        for token in tweet:
            if int(token['offset']) == i:
                if isinstance(token['token'], unicode):
                    utterance += token['token'] + ' '
                else:
                    utterance += str(token['token'])
                break
    return utterance[:-1]


def multiple_tweets_insert(tweets_list, cursor, connection):
    query_tuple = ()
    for tweet in tweets_list:
        tweet_id = tweet.get_tweet_id()
        tweet_text = tweet.get_tweet_text()
        username = tweet.get_username()
        if '\'' in tweet_text:
            tweet_text = tweet_text.replace('\'', '\'\'')
        in_replay_to = str(tweet.get_in_replay_to_id())
        if in_replay_to == 'None ':
            in_replay_to = None
        conversation_id = tweet.get_conversation_id()
        german = check_lang.check_german(tweet_text)
        tweet_tuple = (tweet_id, username, in_replay_to, conversation_id, tweet_text, german)
        query_tuple = (tweet_tuple,) + query_tuple
    query = 'INSERT INTO Tweet (Tweet_id, Username, In_replay_to, Conversation_id, Tweet_text, German) ' \
            'VALUES (%s, %s, %s, %s , %s , %s)'
    cursor.executemany(query, query_tuple)
    connection.commit()


def insert_annotated_table(list_of_tweets, cursor, connection):
    segment_dict_list = list()
    token_dict_list = list()
    ontology_dict = matching_schema.make_ontology_dict(cursor)
    for tweet in list_of_tweets:
        tweet_id = int(tweet.get_tweet_id())
        tokens = tweet.get_tokens()
        segments = tweet.get_segments()
        for offset, token_da in tokens.iteritems():
            token = token_da[0]
            if type(token) is unicode:
                if '\'' in token:
                    token = token.replace('\'', '\'\'')
            da_id_ontologies = ontology_dict[token_da[1]]
            da_id_full = da_id_ontologies[0]
            da_id_reduced = da_id_ontologies[1]
            da_id_min = da_id_ontologies[2]
            token_dict = {'tweet_id': tweet_id, 'offset': offset, 'token': token, 'da_id_full': da_id_full,
                          'da_id_reduced': da_id_reduced, 'da_id_min': da_id_min}
            token_dict_list.append(token_dict)

        for segment, da in segments.iteritems():
            da_id_ontologies = ontology_dict[da]
            da_id_full = da_id_ontologies[0]
            da_id_reduced = da_id_ontologies[1]
            da_id_min = da_id_ontologies[2]
            start_offset = int(segment.split(':')[0])
            end_offset = int(segment.split(':')[1])
            utterance = make_utterance(token_dict_list, tweet_id, start_offset, end_offset)
            segment_dict = {'tweet_id': tweet_id, 'start_offset': start_offset, 'end_offset': end_offset,
                            'utterance': utterance, 'da_id_full': da_id_full,
                            'da_id_reduced': da_id_reduced, 'da_id_min': da_id_min}
            segment_dict_list.append(segment_dict)

    query_segmentation = 'insert into segmentation (tweet_id, start_offset, end_offset, utterance, dialogue_act_id_full, ' \
                         'dialogue_act_id_reduced, dialogue_act_id_min ) values (%(tweet_id)s, %(start_offset)s, ' \
                         '%(end_offset)s, %(utterance)s,%(da_id_full)s, %(da_id_reduced)s, %(da_id_min)s)'
    cursor.executemany(query_segmentation, segment_dict_list)
    connection.commit()
    insert_baseline_prediction_table(segment_dict_list, cursor, connection)


def insert_baseline_prediction_table(segment_dict_list, cursor, connection):
    da_baseline_full_reduced = 'IT_IP_Inform'
    da_baseline_min = 'IT_IP'
    da_id_full = find_da_by_name(da_baseline_full_reduced, fullOntologyTable, cursor)
    da_id_reduced = find_da_by_name(da_baseline_full_reduced, reducedOntologyTable, cursor)
    da_id_min = find_da_by_name(da_baseline_min, minimalOntologyTable, cursor)
    query_predictions = 'insert into segmentation_prediction (Tweet_id, start_offset, end_offset, dialogue_act_id_full, ' \
                        'dialogue_act_id_reduced, dialogue_act_id_min)' \
                        'VALUES (%(tweet_id)s, %(start_offset)s, %(end_offset)s, ' \
                        '%(da_id_full)s, %(da_id_reduced)s, %(da_id_min)s)'
    for segment in segment_dict_list:
        segment['da_id_full'] = da_id_full
        segment['da_id_reduced'] = da_id_reduced
        segment['da_id_min'] = da_id_min
    cursor.executemany(query_predictions, segment_dict_list)
    connection.commit()


