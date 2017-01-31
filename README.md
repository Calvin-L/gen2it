# Generator to Iterator Converter

This tool compiles generator methods to Java-style iterators.

Generator methods are a very convenient way to write code that produces streams
of values: they are normal functions that periodically yield values to the
caller. In many cases it is easier to express a stream of values as a generator
than to manually write an implementation of
[Iterator](https://docs.oracle.com/javase/8/docs/api/java/util/Iterator.html).

For example, a generator method to produce Fibonacci numbers might look like
this:

```
int a = 1;
int b = 1;
while (true) {
    yield(a);     // produce a value
    int prev_a = a;
    a = b;
    b += prev_a;
}
```

## Using the tool

I expect you to be running Python 3. Install dependencies with `pip`:

    $ pip3 install -r requirements.txt

Invoke the tool by running:

    $ python3 -m gen2it INPUT_FILE -o OUTPUT_FILE

The input should be a Java source file with a single class having a
`TypeName generate(args...)` method. That method may call
`yield(TypeName value)` to yield
values. The output is a Java source file with `boolean hasNext()` and
`TypeName next()` methods.

Sample inputs for the tool can be found in the examples folder.

## Usage Notes

 - The generated iterators are not threadsafe. You will need to manually
   synchronize calls to any method on the generated iterator classes.

 - This style of programming can be [faked in pure Java using threads](https://github.com/mherrmann/java-generator-functions),
   however, this tool will avoid the overhead of the extra threads and the risks
   of leaking memory through them.

 - Many features are not yet implemented. Feel free to file issues or open pull
   requests to fix missing functionality. A few things that may not work
   properly yet:
    - try-catch and try-with-resources
    - for-loops
    - using a for-each loop over an array
