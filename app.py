'''
Issue Tracker
Author: Amartya Vadlamani
Org: Young Scientists Journal (ysjournal.com)
'''

from flask import Flask, request
from flask_restful import Resource, Api
import json
from uuid import uuid4
app = Flask(__name__)
api = Api(app)

class JsonBackedList:
    def __init__(self, json_loc):
        self.json_loc = json_loc
        self.mem_list = []
        self.load()
    def load(self):
        self.mem_list = json.load(open(self.json_loc))
    def save(self):
        json.dump(self.mem_list, open(self.json_loc, "w"))
    def __getitem__(self, index):
        self.load()
        return self.mem_list.__getitem__(index)
    def __setitem__(self, index, item):
        self.mem_list.__setitem__(index, item)
        self.save()
    def __delitem__(self, index):
        self.mem_list.__delitem__(index)
        self.save()
    def append(self, item):
        self.mem_list.append(item)
        self.save()

issues_list = JsonBackedList("issues.json")

class Issues(Resource):
    
    def list(self, args):
        ret_str = "*Issues*\n"
        
        ret_str += "_Unresolved_\n"
        for item in issues_list:
            if not item["resolved"]:
                ret_str += str(item["id"])+"-"+item["title"]+"\n"
        
        ret_str += "_Resolved_\n"
        for item in issues_list:
            if item["resolved"]:
                ret_str += str(item["id"])+"-"+item["title"]+"\n"
        
        return ret_str
    def modify_issue_with_id(self, id, f):
        for index, item in enumerate(issues_list):
            if item["id"] == id:
                issues_list[index] = f(item)
    def get_issue_with_id(self, id):
        for item in issues_list:
            if item["id"] == id:
                return item
        
    def claim(self, args):
        def claim_func(issue):
            issue["owner"] = request.values["user_name"]
            return issue
        
        def unclaim_func(issue):
            issue["owner"] = None
            return issue
         
        issue = self.get_issue_with_id(args[0])
        if issue["owner"] != None:
            if issue["owner"] == request.values["user_name"]:
                self.modify_issue_with_id(args[0], unclaim_func)
                return "You are now no longer the owner of issue: " + issue["title"]
            else:
                return "Someone else is incharge of that issue, ask them nicely to stop working on it."
        else:
            self.modify_issue_with_id(args[0], claim_func)
            return "Ok, Cool. You're now in charge of" + issue["title"]
            
    def resolve(self, args):
        def resolve_func(issue):
            issue["resolved"] = True
            return issue
        issue = self.get_issue_with_id(args[0])
        if issue["owner"] == request.values["user_name"]:
            self.modify_issue_with_id(args[0], resolve_func)
            return "Yay! " + issue["title"] + " is done."
        else:
            return "Someone else is incharge of this, see who it is with `/issues details "+ issue["id"] +"` and contact them"
            
    def create(self, args):
        title, description, urgency = args
        id = uuid4().hex[:10]
        resolved, owner = False, None
        issues_list.append({
            "id": id,
            "title": title,
            "description": description,
            "urgency": urgency,
            "resolved": resolved,
            "owner": owner,
            })
        return "Created issue " + title
    def delete(self, args):
        id = args[0]
        for index, item in enumerate(issues_list):
            if item["id"] == id:
                del item
    def details(self, args):
        issue = self.get_issue_with_id(args[0])
        detail = "*RESOLVED*\n" if issue["resolved"] else ""
        detail += "_{title}_\n\n{description}\nUrgency: {urgency}\n".format(**issue)
        detail += "Owned By {owner}".format(**issue) if issue["owner"] else "Unowned"
        return detail
        
    def dispatch(self):
        user_class_to_response = {
            "tech": "Your relevent commands are `list` `details` `claim` `resolve`. You can get more help by using `/issues help <command>`",
            "non-tech": "Your relevent commands are `list` `details` `create` `delete`. You can get more help by using `/issues help <command>`",
            "list": "syntax is `/issues list <optional-id>`, it will list all current issues and if an issue id is included it will only show that",
            "claim": "syntax is `/issues claim <issue-id>`, claim ownership of the issue. This means that you will be the one who resolves the issue",
            "resolve": "syntax is `/issues resolve <issue-id>, <resolve-msg>, the issue `<issue-id>` is resolved and the message `<resolve-msg>` is the reason for resolution. e.g. fixed, intended, not a bug",
            "create": "syntax is `/issues create <title>, <description>, <urgency>`, create an issue with a given `title`, `description` and `urgency`",
            "delete": "syntax is `/issues delete <issue-id>`, deletes an issues. Note: this **does not resolve** it",
            "details": "syntax is `/issues details <issue-id>`, displays the details of a issue",
            "": "Hello I am `issues-bot`, I am here to keep track of all of your technical problems. If you are a part of the technical team use `/issues help tech`, otherwise use `/issues help non-tech`. *NOTE*: All messages are private (cannot be seen by others) unless you put the word `public` at the end of our command. e.g. `/issues list public`"
            }
        values = request.values
        if " " in values["text"]:
            command, args = values["text"].split(" ", 1)
        else:
            command, args = values["text"], ""
        args = [arg.strip() for arg in args.split(",")]
        public = False
        if len(args) > 0 and args[-1] == "public":
            args = args[:-1]
            public = True
        if command == "help":
            if args[0] == "all" or args[0] not in user_class_to_response.keys():
                return public, "\n".join(["+ *"+key+"*: "+value for key, value in sorted(user_class_to_response.items())])
            else:
                return public, user_class_to_response[args[0]]
        else:
            try:
                return public, getattr(self, command)(args)
            except:
                if command not in user_class_to_response.keys():
                    return public, "That is not a supported command look at `/issues help all` for a list of valid commands"
                return public, "There was an error did you look at the help?\n\n" + user_class_to_response[command]

    def post(self):
        #try:
        public, text = self.dispatch()
        #except:
        #    return "Something when wrong in the `dispatch` method, please let your nearest web-development team member know"
        return {
            "response_type": "in_channel" if public else "ephemeral",
            "text": text,
            "mrkdwn": True
            }
        
api.add_resource(Issues, '/')

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)