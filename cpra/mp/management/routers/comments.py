# GET /management/v1/comments/?task_id=1001
#
# GET /management/v1/comments/1002/replies
#
# POST /management/v1/comments
# {
#     "task_id": 1001,
#     "commentText": "Hello world",
#     "assignees": [1000],
#     "notifyAll": true
# }
#
# POST /management/v1/comments/1002/replies
# {
#     "commentText": "Hello world",
#     "assignees": [1000],
#     "notifyAll": true,
# }
#
# PUT /management/v1/comments/1002
# {
#     "commentText": "New comment text",
# }