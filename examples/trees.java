import java.util.Iterator;
import java.util.Stack;

public class TreeIterator implements Iterator<Integer> {

    public static class Node {
        int value;
        Node left;
        Node right;
    }

    Integer generate(Node root) {
        Stack<Node> toExplore = new Stack<>();
        toExplore.push(root);
        while (!toExplore.isEmpty()) {
            Node n = toExplore.pop();
            yield(n.value);
            if (n.left != null) toExplore.push(n.left);
            if (n.right != null) toExplore.push(n.right);
        }
    }

}
