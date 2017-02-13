import praw
import prawcore
import numpy as numpyimport
import matplotlib.pyplot as pyplot
import nltk
import markovify
import pickle

debug = False

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

		# Fetches the latest comments by an user, places an ending character at the end
		# of each comment if one is not already there, and concatenates all comments together
		# for later generation of Markov model.
		comments = self.reddit.redditor(user).comments.new(limit = 1000)
		for comment in comments:
			body = comment.body
			if not self.isEnder(body[-1]):
				body += ('.')
			userComments.append(body)

		# Stores the comments for later, since Reddit API calls are expensive.
		chainGenerator.storage[user] = userComments

	# Generates a markov model 
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

	# Uses Markov model to generate a simulated comment
	def speak(self, users):
		self.generateModel(users)
		return "MarkComp Bot: " + chainGenerator.models[users].make_sentence()

	# Checks if the given user exists.
	def user_exists(self, user):
		exists = True
		try:
			self.reddit.redditor(user).fullname
		except prawcore.exceptions.NotFound:
			exists = False
		return exists

	# Checks if the summon contains a valid user list. All users must be valid.
	def validUsers(self, comment):
		splitted = comment.split()
		userCount = len(splitted) - 1
		allUsers = []
		if debug:
			print("Validity checking...")
		if userCount >= 1 and userCount <= 3:
			for potentialUser in splitted[1:]:
				if self.user_exists(potentialUser):
					allUsers.append(potentialUser)
			return len(allUsers) == userCount

	# Extracts the user list from the comment.
	def extractUsers(self, comment):
		if debug:
			print("Extracting")
		return comment.split()[1:]

	# Checks if the comment contains a summon.
	def wasSummoned(self, comment):
		if debug:
			print("Summon Check")
		splitted = comment.split()
		if len(splitted) >= 1:
			if splitted[0] == "markov:":
				return True
		return False

	# Monitors the The_Summoning_Pit's comment stream.
	def monitor(self):
		search = False
		latest = ""
		try:
			latest = open(r'latest.pkl', 'rb')
			latest = pickle.load(latest)
			search = True
		except:
			latest = ""
		for comment in self.reddit.subreddit('The_Summoning_Pit').stream.comments():
			if debug:
				print(comment.body)

			if search == True and comment == latest:
				search = False
			elif search == False:
				body = comment.body
				if debug:
					print("body: " + body)
				if self.wasSummoned(body):
					if self.validUsers(body):
						users = self.extractUsers(body)
						self.reply(comment, users)
					else:
						print("Commenting on failure...")
						comment.reply("Invalid Summon. Must contain 1-3 space-separated usernames.")
				latest = comment
				outfile = open(r'latest.pkl', 'wb')
				pickle.dump(latest, outfile)

	# Replies to the comment
	def reply(self, comment, users):
		if debug:
			print("Replying...")
		users = tuple(users) # Convert to tuple because 'users' needs to be a hashable set.
		spoken = self.speak(users)
		comment.reply(spoken)

def main():
	credentials = open(r'credentials.pkl', 'rb')
	credentials = pickle.load(credentials)
	clientId = credentials[0]
	clientSecret = credentials[1]
	password = credentials[2]
	agent = credentials[3]
	user = credentials[4]
	reddit = obtainRedditInstance(clientId, clientSecret, password, agent, user)
	generator = chainGenerator(reddit)
	generator.monitor()

if __name__ == "__main__":
	main()