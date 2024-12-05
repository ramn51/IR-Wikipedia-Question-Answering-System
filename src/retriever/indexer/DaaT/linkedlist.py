'''
@author: Sougata Saha
Institute: University at Buffalo
'''

import math


class Node:

    def __init__(self, value=None, next=None):
        """ Class to define the structure of each node in a linked list (postings list).
            Value: document id, Next: Pointer to the next node
            Add more parameters if needed.
            Hint: You may want to define skip pointers & appropriate score calculation here"""
        self.value = value
        self.next = next
        self.skip  = None


class LinkedList:
    """ Class to define a linked list (postings list). Each element in the linked list is of the type 'Node'
        Each term in the inverted index has an associated linked list object.
        Feel free to add additional functions to this class."""
    def __init__(self):
        self.start_node = None
        self.end_node = None
        self.length, self.n_skips, self.idf = 0, 0, 0.0
        self.skip_length = None

    def traverse_list(self):
        traversal = []
        if self.start_node is None:
            return
        else:
            """ Write logic to traverse the linked list.
                To be implemented."""
            current_node = self.start_node

            while current_node is not None:
                # print(current_node.value)
                traversal.append(current_node.value)
                current_node = current_node.next

            return traversal, self.start_node

    def traverse_skips(self):
        traversal = []
        if self.start_node is None:
            return
        else:
            """ Write logic to traverse the linked list using skip pointers.
                To be implemented."""
            current_node = self.start_node

            while current_node:
                # print(current_node.value)
                traversal.append(current_node.value)
                if current_node.skip:
                    current_node = current_node.skip
                else:
                    break

            return traversal

    def add_skip_connections(self):
        n_skips = int(round(math.sqrt(self.length)))
        # if n_skips * n_skips == self.length:
        #     n_skips = n_skips - 1
        """ Write logic to add skip pointers to the linked list. 
            This function does not return anything.
            To be implemented."""
        self.skip_length = n_skips

        if self.length <= 2:
            return
        
        dist_between_skips = int(round(math.sqrt(self.length)))
        # print(f"distance between skips: {distance_between_skips}")
        current = self.start_node
        prev_skip = self.start_node
        c = 0
        while current:
            if c == dist_between_skips:
                if prev_skip:
                    prev_skip.skip = current
                prev_skip = current
                c = 0
            current = current.next
            c+=1

        # current = self.start_node

        # for i in range(self.skip_length):
        #     if current:
        #         current = current.next
        #     else:
        #         break

        
        # skip_curr = self.start_node

        # while current and current.next:
        #     skip_curr.skip = current.next
        #     for i in range(self.skip_length):
        #         if current:
        #             current = current.next
        #     skip_curr = skip_curr.skip
            
            # skip_curr = skip_curr.skip

    def insert_at_end(self, value, criteria='doc_id'):
        """ Write logic to add new elements to the linked list.
            Insert the element at an appropriate position, such that elements to the left are lower than the inserted
            element, and elements to the right are greater than the inserted element.
            To be implemented. """
        new_node = Node(value)
        if criteria == 'doc_id':
            tuple_index = 0 # doc_id
        else:
            tuple_index = 3 # tf-idf
            # print("NEW NODE: ", new_node.value[tuple_index]) 

               
        if not self.start_node or self.start_node.value[tuple_index] > value[tuple_index]:
            # print("SELF START NODE: ", self.start_node.value[tuple_index])
            new_node.next = self.start_node
            self.start_node = new_node
            self.end_node = new_node
            self.length += 1
            return
        else:
            curr_node = self.start_node
            
            while curr_node.next and curr_node.next.value[tuple_index] < value[tuple_index]:
                curr_node = curr_node.next

            new_node.next = curr_node.next
            curr_node.next = new_node
            self.length += 1
            return

