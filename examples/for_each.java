import java.util.Iterator;
import java.util.Arrays;

public class MyIterator implements Iterator<Integer> {
    Integer generate(List<Integer> arg) {
        for (Integer i : arg) {
            yield(i);
        }
    }
}
