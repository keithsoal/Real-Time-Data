float randNum;
float val;
float counter = 0;
float pi = 3.14;
float f1 = 10;
float f2 = 20;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
}

void loop() {
  // put your main code here, to run repeatedly:
  randNum = random(100)/10;
  val = 5*sin(2*pi*f1*(counter/200)) + 5*sin(2*pi*f2*(counter/200)) + randNum;
  Serial.println(val);
  counter += 1;
  delay(5);
}
