def count_files_in_tree(tree_data):
    count = 0
    for item in tree_data:
        if item['type'] == 'file':
            count += 1
        elif item['type'] == 'directory' and 'children' in item:
            count += count_files_in_tree(item['children'])
    return count