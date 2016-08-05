

processes = {
    "123": {
    },
    "456": {
    },
    "789": {
    },

}


def get_root():
    # TODO: check why we can not return just processes.keys()
    return [
        i for i, j in processes.items()
        if not j.get('deleted')
    ]


def get_process(uid):
    if uid in processes:
        return processes[uid]

    return 'Process "{}" not found'.format(uid), 404


def post_process(uid, process):
    if uid not in processes:
        processes[uid] = process
        return 'Process "{}" started'.format(uid)

    return 'Process "{}" already exists'.format(uid), 404


def delete_process(uid):
    if uid in processes:
        processes[uid]['deleted'] = True
        # TODO: do callback to "main" process
        return 'Process "{}" marked for deletion'.format(uid)

    return 'Process "{}" not found'.format(uid), 404


def patch_process(uid, process):
    if uid in processes:
        processes[uid]['result'] = process
        # TODO: validate
        delete_process(uid)
        return 'Process "{}" marked for deletion'.format(uid)

    return 'Process "{}" not found'.format(uid), 404
