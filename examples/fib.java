import java.util.Iterator;
public class FibonacciIterator implements Iterator<Integer> {
    Integer generate() {
        int a = 1;
        int b = 1;
        while (true) {
            yield(a);
            int tmp = a;
            a = b;
            b += tmp;
        }
    }
}
