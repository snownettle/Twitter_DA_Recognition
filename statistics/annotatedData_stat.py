__author__ = 'snownettle'

# from postgres import postgres_queries
# from twitter_objects.conversation import Conversation


def number_of_annotated_tweet(list_of_tweets):
    print 'There are ', len(list_of_tweets), ' annotated tweets by linguistic students in DB'


def numbers_of_tweets_agreed_by_three(agreed_with_segmentation, agreed_with_tags):
    print 'The students are agreed with segmentation for ', agreed_with_segmentation, 'of tweets'
    print 'The students are agreed with tags for ', len(agreed_with_tags), 'of tweets'


def numbers_of_agreed_tweets_after_merging(list_of_tweets, agreed):
    argeed_with_tags = 0
    list_of_tweets_for_editing = list()
    list_of_tweets_done = list()
    for tweet in list_of_tweets:
        same_decision = 0
        token_dictionary = tweet.get_tags()
        token_number = len(token_dictionary)
        for offset, tags in token_dictionary.iteritems():
            if len(tags) == 1:
                same_decision += 1
        if same_decision == token_number:
            argeed_with_tags += 1
            list_of_tweets_done.append(tweet)

        else:
            list_of_tweets_for_editing.append(tweet)
    print 'After merging there are ' + str(len(list_of_tweets_done) + len(agreed)) + ' done tweets'
    print 'There are ' + str(len(list_of_tweets_for_editing)) + ' to edit'
    return list_of_tweets_done, list_of_tweets_for_editing


#rewrite!

# def segments_in_tweet(list_of_annotated_tweets):
#     number_of_segments = dict()
#     average_number_of_tweets = list()
#     overal_segments = int()
#     for tweet in list_of_annotated_tweets:
#         segments = tweet.get_segmentation()
#         occurancy = len(segments)
#         if occurancy in number_of_segments:
#             number_of_segments[occurancy] += 1
#         else:
#             number_of_segments[occurancy] = 1
#     for number, value in number_of_segments.iteritems():
#         print 'Number of segments: ', number, ' occur: ', value, ' times'

def unigrams_raw_annotation(list_of_annotated_tweets):
    number_of_unigrams = dict()
    for tweet in list_of_annotated_tweets:
        tags = tweet.get_tags()
        for segment, tag in tags.iteritmes:
            if segment in number_of_unigrams:
                number_of_unigrams[segment] += 1
            else:
                number_of_unigrams[segment] = 1
    for tag_name, occurancy in number_of_unigrams.iteritems():
        print tag_name + '; ' + occurancy
    # return number_of_unigrams




