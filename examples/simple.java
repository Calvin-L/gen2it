import java.util.Iterator;
import java.util.Arrays;

public class MyIterator implements Iterator<Integer> {
    Integer generate(int arg) {
        yield(1);
        int x = 0;
        while (x < 10) {
            yield(x);
            x += 1;
        }
        for (Integer i : Arrays.asList(1, 2, 3, 4)) {
            yield(i);
        }

        java.util.Iterator<Integer> it = Arrays.asList(1, 2, 3, 4).iterator();
        while (it.hasNext()) {
            Integer i = it.next();
            yield(i);
        }
    }
}
