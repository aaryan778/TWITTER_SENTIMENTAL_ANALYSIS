from tweepy import API
from tweepy import Cursor
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from os import path
from textblob import TextBlob
from PIL import Image
import twitter_credentials
from wordcloud import WordCloud, ImageColorGenerator
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import re
import seaborn as sns
import spacy
import nltk
import csv
nlp = spacy.load('en_core_web_lg')

# # # # TWITTER CLIENT # # # #
class TwitterClient():
    def __init__(self, twitter_user=None):
        self.auth = TwitterAuthenticator().authenticate_twitter_app()
        self.twitter_client = API(self.auth)

        self.twitter_user = twitter_user

    def get_twitter_client_api(self):
        return self.twitter_client

    def get_user_timeline_tweets(self, num_tweets,i=1):
        tweets = []
        for tweet in Cursor(self.twitter_client.user_timeline, id=self.twitter_user).items(num_tweets):
            tweets.append(tweet)
            i=i+1
        return tweets

    def get_friend_list(self, num_friends,l=[]):
        friend_list = []
        for friend in Cursor(self.twitter_client.friends, id=self.twitter_user).items(num_friends):
            friend_list.append(friend)
        return friend_list

    def get_home_timeline_tweets(self, num_tweets):
        home_timeline_tweets = []
        for tweet in Cursor(self.twitter_client.home_timeline, id=self.twitter_user).items(num_tweets):
            home_timeline_tweets.append(tweet)
        return home_timeline_tweets


# # # # TWITTER AUTHENTICATER # # # #
class TwitterAuthenticator():

    def authenticate_twitter_app(self):
        auth = OAuthHandler(twitter_credentials.CONSUMER_KEY, twitter_credentials.CONSUMER_SECRET)
        auth.set_access_token(twitter_credentials.ACCESS_TOKEN, twitter_credentials.ACCESS_TOKEN_SECRET)
        return auth

# # # # TWITTER STREAMER # # # #
class TwitterStreamer():
    """
    Class for streaming and processing live tweets.
    """
    def __init__(self):
        self.twitter_autenticator = TwitterAuthenticator()

    def stream_tweets(self, fetched_tweets_filename, hash_tag_list):
        # This handles Twitter authetification and the connection to Twitter Streaming API
        listener = TwitterListener(fetched_tweets_filename)
        auth = self.twitter_autenticator.authenticate_twitter_app()
        stream = Stream(auth, listener)

        # This line filter Twitter Streams to capture data by the keywords:
        stream.filter(track=hash_tag_list)


# # # # TWITTER STREAM LISTENER # # # #
class TwitterListener(StreamListener):
    """
    This is a basic listener that just prints received tweets to stdout.
    """
    def __init__(self, fetched_tweets_filename):
        self.fetched_tweets_filename = fetched_tweets_filename

    def on_data(self, data):
        try:
            print(data)
            with open(self.fetched_tweets_filename, 'a') as tf:
                tf.write(data)
            return True
        except BaseException as e:
            print("Error on_data %s" % str(e))
        return True

    def on_error(self, status):
        if status == 420:
            # Returning False on_data method in case rate limit occurs.
            return False
        print(status)


class TweetAnalyzer():
    """
    Functionality for analyzing and categorizing content from tweets.
    """

    def clean_tweet(self, tweet):
        return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())

    def analyze_sentiment(self, tweet):
        analysis = TextBlob(self.clean_tweet(tweet))

        if analysis.sentiment.polarity > 0:
            return 1
        elif analysis.sentiment.polarity == 0:
            return 0
        else:
            return -1


    def tweets_to_data_frame(self, tweets):
        df = pd.DataFrame(data=[tweet.text for tweet in tweets], columns=['tweets'])

        df['id'] = np.array([tweet.id for tweet in tweets])
        df['len'] = np.array([len(tweet.text) for tweet in tweets])
        df['date'] = np.array([tweet.created_at for tweet in tweets])
        df['source'] = np.array([tweet.source for tweet in tweets])
        df['likes'] = np.array([tweet.favorite_count for tweet in tweets])
        df['retweets'] = np.array([tweet.retweet_count for tweet in tweets])
        return df


if __name__ == '__main__':

    twitter_client = TwitterClient()
    tweet_analyzer = TweetAnalyzer()

    api = twitter_client.get_twitter_client_api()

    tweets = api.user_timeline(screen_name="CNN", count=200)
    df = tweet_analyzer.tweets_to_data_frame(tweets)
    df['sentiment'] = np.array([tweet_analyzer.analyze_sentiment(tweet) for tweet in df['tweets']])
    print(df.head(19))
    df.to_csv('CNN.csv',encoding='utf-8')

    f = pd.read_csv("CNN.csv")
    keep_col = ['sentiment']
    new_f = f[keep_col]
    new_f.to_csv("CNNUpd.csv", index=False)

    x = pd.read_csv("CNNUpd.csv")
    y = pd.value_counts(df['sentiment'])
    print(y)

#MATPLOTLIB GRAPHS BETWEEN LIKES/RETWEETS
    time_likes = pd.Series(data=df['likes'].values, index=df['date'])
    time_likes.plot(figsize=(16, 4), label="likes", legend=True)

    time_retweets = pd.Series(data=df['retweets'].values, index=df['date'])
    time_retweets.plot(figsize=(16, 4), label="retweets", legend=True)
    plt.show()

    #GENERATING WORDCLOUD FOR TWEETS

    mask = np.array(Image.open("twitter_mask.png"))
    allWords = ' '.join( [twts for twts in df['tweets']] )

    wordCloud = WordCloud(background_color="white", mask=mask, mode="RGB", width = 1600, height=800, random_state = 21, max_font_size=119).generate(allWords)
    plt.imshow(wordCloud, interpolation = "bilinear")

    plt.axis('off')
    plt.show()

    #TOP_WORDS_OF_SCREEN_NAME
    list_of_sentences = [sentence for sentence in df.tweets]
    lines=[]
    for sentence in list_of_sentences:
        words = sentence.split()
        for w in words:
            lines.append(w)

    lines = [re.sub(r"(@[A-Za-z0-9]+)|(\w+:\/\/\S+)","",x) for x in lines]
    lines2 = []
    for word in lines:
        if word!='':
            lines2.append(word)

    from nltk.stem.snowball import SnowballStemmer
    s_stemmer = SnowballStemmer(language='english')
    stem=[]
    for word in lines2:
        stem.append(s_stemmer.stem(word))

    stem2 = []
    for word in stem:
        if word not in nlp.Defaults.stop_words:
            stem2.append(word)

    df2 = pd.DataFrame(stem2)
    df2 = df2[0].value_counts()
    df2 = df2[:20,]
    plt.figure(figsize=(20,10))
    sns.barplot(df2.values, df2.index, alpha=0.8)
    plt.title('Top Words Overall')
    plt.ylabel('Word from Tweet', fontsize=12)
    plt.xlabel('Count of Words', fontsize=12)
    plt.show()

    #TOP_ORGANIZATIONS_MENTIONED_IN_SCREENNAME
    def show_ents(doc):
        if doc.ents:
            for ent in doc.ents:
                print(ent.text + '-' + ent.label_+ '-'+ str(spacy.explain(ent.label_)))

    str1 = " "
    stem2 = str1.join(lines2)
    stem2 = nlp(stem2)
    label = [(X.text, X.label_) for X in stem2.ents]
    df6 = pd.DataFrame(label, columns = ['Word', 'Entity'])
    df7 = df6.where(df6['Entity'] == 'ORG')
    df7 = df7['Word'].value_counts()
    dfx = df7[:20,]
    plt.figure(figsize=(30,10))
    sns.barplot(dfx.values, dfx.index, alpha=1)
    plt.title('Top Organizations Mentioned')
    plt.ylabel('Word from Tweet', fontsize=12)
    plt.xlabel('Count of Words', fontsize=12)
    plt.show()

    #TOP_PEOPLE_MENTIONED
    str2 = " "
    stem2 = str1.join(lines2)
    stem2 = nlp(stem2)
    label = [(X.text, X.label_) for X in stem2.ents]
    df6 = pd.DataFrame(label, columns = ['Word', 'Entity'])
    df7 = df6.where(df6['Entity'] == 'PERSON')
    df7 = df7['Word'].value_counts()
    dfx = df7[:20,]
    plt.figure(figsize=(30,10))
    sns.barplot(dfx.values, dfx.index, alpha=0.8)
    plt.title('Top People Mentioned')
    plt.ylabel('Word from Tweet', fontsize=12)
    plt.xlabel('Count of Words', fontsize=12)
    plt.show()