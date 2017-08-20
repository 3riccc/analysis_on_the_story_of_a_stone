import suffix_tree
import copy
import math

split_mark = "#"

friendly_split_mark = "，"
word_split_mark = "/"

input_file = open("preprocessing.txt", "r")
output_file = open("dict.csv", "w")

MIN_COUNT = 5
MIN_ENTROPY = 1.
MIN_SCORE = 100.
MIN_CO = 1.


def load():
    return input_file.read()


def construct_tree(string):
    tree = suffix_tree.SuffixTree(string + "$")
    tree.update_counter()
    return tree


def count_sentence_length(string):
    sentences = string.split(split_mark)
    length = [len(string) for string in sentences]
    max_length = max(length)

    count = [0]*(max_length+1)
    for l in length:
        count[l] += 1

    return count


def count_all_possibilities(sentence_length_count, word_length):
    count_sum = 0
    for length, count in enumerate(sentence_length_count):
        if length >= word_length:
            count_sum += count*(length - word_length + 1)
    return count_sum


def new_cursor(tree, branch):
    return suffix_tree.Cursor(tree.root, branch, 0, tree.root)


def entropy_of_list(nodes):
    node_counts = [node.counter if str(node)[0] != split_mark else 1.
                   for node in nodes]
    count_sum = sum(node_counts)
    probs = [count/count_sum for count in node_counts]

    entropy = -sum([prob*math.log(prob, 2) for prob in probs])

    for node in nodes:
        if str(node)[0] == split_mark \
              and node.counter >= 0.5 * count_sum + node.counter - 1:
            return max(entropy, MIN_ENTROPY + 0.00001)

    return entropy


def mark_words(tree, reversed_tree, count_of_length, cursor, string):
    if split_mark in string:
        return

    if cursor.current_node.counter >= MIN_COUNT:
        if len(string) > 1:
            p_no_split = cursor.current_node.counter/count_of_length[len(string)]

            left_part = new_cursor(tree, string[0])
            right_part = copy.copy(cursor)
            right_part.move_front_forward(string[0])

            p_split = []

            for i in range(1, len(string)):
                p_left = left_part.current_node.counter/count_of_length[i]
                p_right = right_part.current_node.counter/count_of_length[len(string) - i]
                p_split.append(p_left*p_right)

                if i != len(string) - 1:
                    left_part.move_forward(string[i])
                    right_part.move_front_forward(string[i])

            co = p_no_split/max(p_split)

            if co >= MIN_CO:
                reverse_lookup = reversed_tree.query_cursor(string[::-1])
                if reverse_lookup.length + 1 == len(reverse_lookup.current_node):
                    left_entropy = entropy_of_list(reverse_lookup.current_node.next.values())
                else:
                    left_entropy = 0
                right_entropy = entropy_of_list(cursor.current_node.next.values())

                score = co*(left_entropy+right_entropy)

                if score > MIN_SCORE and left_entropy > MIN_ENTROPY and right_entropy > MIN_ENTROPY:
                    output_file.write("%s,%d,%f,%f,%f,%f,%f\n" % (string, cursor.current_node.counter, co, left_entropy, right_entropy, left_entropy+right_entropy, score))

        for key, child in cursor.current_node.next.items():
            next_cursor = suffix_tree.Cursor(cursor.current_node, key, len(child), tree.root)
            mark_words(tree, reversed_tree, count_of_length, next_cursor, string + str(next_cursor.current_node))


def main():
    string = load()
    print("Building tree")
    tree = construct_tree(string)
    print("Building reversed tree")
    reversed_tree = construct_tree(string[::-1])

    print("Counting sentences")
    sentence_length_count = count_sentence_length(string)
    count_of_length = [count_all_possibilities(sentence_length_count, i)
                       for i in range(len(sentence_length_count))]
    print("Finding words")
    for key, child in tree.root.next.items():
        cursor = suffix_tree.Cursor(tree.root, key, len(child), tree.root)
        mark_words(tree, reversed_tree, count_of_length, cursor, str(cursor.current_node))

if __name__ == "__main__":
    # test_cursor()
    main()
