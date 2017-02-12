import praw
import prawcore
import numpy as numpyimport
import matplotlib.pyplot as pyplot
import nltk
import markovify

debug = True

# Returns instance of Reddit with supplied credentials
def obtainRedditInstance(clientId, clientSecret, password, agent, user):
	reddit = praw.Reddit(client_id = clientId,
                     client_secret = clientSecret,
                     password = password,
                     user_agent = agent,
                     username = user)
	return reddit

class chainGenerator:

	storage = {}
	models = {}

	def __init__(self, reddit):
		self.reddit = reddit

	def dumpStorage(self):
		chainGenerator.storage = {}

	def dumpModels(self):
		chainGenerator.models = {}

	def isEnder(self, character):
		return character == '.' or character == '?' or character == '!'

	# Builds the the models for all requested users.
	def fetchComments(self, user):
		if user in chainGenerator.storage:
			return
		userComments = []
		comments = self.reddit.redditor(user).comments.new(limit = 1000)
		for comment in comments:
			body = comment.body
			if not self.isEnder(body[-1]):
				body += ('.')
			userComments.append(body)
		chainGenerator.storage[user] = userComments

	def generateModel(self, users):
		if users in chainGenerator.models:
			return
		allComments = ""
		for user in users:
			self.fetchComments(user)
			userComments = chainGenerator.storage[user]
			allComments += " ".join(userComments) + " "
		model = markovify.Text(allComments)
		chainGenerator.models[users] = model

	def speak(self, users):
		if users not in chainGenerator.models:
			self.generateModel(users)
		return "MarkComp Bot: " + chainGenerator.models[users].make_sentence()

	def user_exists(self, user):
		exists = True
		try:
			self.reddit.redditor(user).fullname
		except prawcore.exceptions.NotFound:
			exists = False
		return exists

	def validUsers(self, comment):
		splitted = comment.split()
		size = len(splitted)
		allUsers = []
		if debug:
			print("Validity Checking")
		if size >= 1 and size <= 5:
			for potentialUser in splitted[1:]:
				if self.user_exists(potentialUser):
					allUsers.append(potentialUser)
			return len(allUsers) == size - 1

	def extractUsers(self, comment):
		if debug:
			print("Extracting")
		return comment.split()[1:]

	def wasSummoned(self, comment):
		if debug:
			print("Summon Check")
		splitted = comment.split()
		if len(splitted) >= 1:
			if splitted[0] == "markov:":
				return True
		return False

	def monitor(self):
		search = False
		for comment in self.reddit.subreddit('The_Summoning_Pit').stream.comments():
			print(comment.body)
			if search and comment == latest:
				search = False
			else:
				body = comment.body
				if debug:
					print("body: " + body)
				if self.wasSummoned(body):
					if self.validUsers(body):
						users = self.extractUsers(body)
						self.reply(comment, users)
				latest = comment

	def reply(self, comment, users):
		if debug:
			print("Replying...")
		users = tuple(users)
		spoken = self.speak(users)
		comment.reply(spoken)


def main():
	reddit = obtainRedditInstance(*CREDENTIALS REMOVED*)
	generator = chainGenerator(reddit)
	generator.monitor()

if __name__ == "__main__":
	main()



