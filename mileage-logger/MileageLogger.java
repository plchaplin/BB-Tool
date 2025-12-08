import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public class MileageLogger {

    private static final String CSV_FILE = "mileage.csv";
    private static final String CSV_HEADER = "Date,Miles";

    public static void main(String[] args) {
        if (args.length == 0) {
            printUsage();
            return;
        }

        String command = args[0];

        switch (command) {
            case "add":
                if (args.length != 3) {
                    printUsage();
                } else {
                    addMileage(args[1], args[2]);
                }
                break;
            case "list":
                listMileage();
                break;
            default:
                printUsage();
                break;
        }
    }

    private static void addMileage(String date, String milesStr) {
        try {
            Double.parseDouble(milesStr);
        } catch (NumberFormatException e) {
            System.err.println("Error: Invalid number for miles.");
            printUsage();
            return;
        }

        File file = new File(CSV_FILE);
        boolean fileExists = file.exists();

        try (BufferedWriter bw = new BufferedWriter(new FileWriter(file, true))) {
            if (!fileExists || file.length() == 0) {
                bw.write(CSV_HEADER);
                bw.newLine();
            }
            bw.write(date + "," + milesStr);
            bw.newLine();
            System.out.println("Mileage added successfully.");
        } catch (IOException e) {
            System.err.println("Error writing to file: " + e.getMessage());
        }
    }

    private static void listMileage() {
        File file = new File(CSV_FILE);
        if (!file.exists()) {
            System.out.println("No mileage records found.");
            return;
        }

        List<String> records = new ArrayList<>();
        try (BufferedReader br = new BufferedReader(new FileReader(file))) {
            String line;
            while ((line = br.readLine()) != null) {
                records.add(line);
            }
        } catch (IOException e) {
            System.err.println("Error reading file: " + e.getMessage());
            return;
        }

        if (records.isEmpty()) {
            System.out.println("No mileage records found.");
        } else {
            for (String record : records) {
                System.out.println(record);
            }
        }
    }

    private static void printUsage() {
        System.out.println("Usage:");
        System.out.println("  java MileageLogger add <date> <miles>");
        System.out.println("  java MileageLogger list");
    }
}
