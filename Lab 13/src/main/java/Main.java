import com.mongodb.MongoClientSettings;
import com.mongodb.MongoCredential;
import com.mongodb.MongoException;
import com.mongodb.ServerAddress;
import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoClients;
import com.mongodb.client.MongoDatabase;
import org.bson.Document;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

import static com.mongodb.client.model.Filters.eq;
import static com.mongodb.client.model.Updates.set;

/**
 * Лабораторная работа №13, вариант 2 (Библиотека).
 * Программа сама готовит базу (администратор, данные, роли, пользователи) и проверяет RBAC.
 * Сервер: mongod на порту 27018, запущенный с ключом --auth.
 * Учебные пароли локального стенда прописаны в коде: перед сдачей и публикацией на GitHub удалите их.
 */
public class Main {

    static final int PORT = 27018;
    static final String DB = "library_lab13";

    static final String ADMIN_USER = "labadmin";
    static final String ADMIN_PWD = "LabAdmin2026";
    static final String PW_VIEWER = "LibViewer2026";
    static final String PW_EDITOR = "LibEditor2026";
    static final String PW_AUDITOR = "LibAuditor2026";

    static int passed = 0;
    static int total = 0;

    public static void main(String[] args) {
        try {
            setup();
        } catch (Exception e) {
            System.out.println("Настройка базы не удалась: " + e.getMessage());
            System.out.println("Проверьте, что окно PowerShell с mongod (порт 27018) открыто и работает.");
            return;
        }
        System.out.println();
        runTests();
    }

    // ------------------------------------------------------------ подготовка базы

    static List<Document> docs(String... json) {
        List<Document> list = new ArrayList<>();
        for (String j : json) list.add(Document.parse(j));
        return list;
    }

    static void createRole(MongoDatabase d, String role, String collection, String... actions) {
        Document privilege = new Document("resource", new Document("db", DB).append("collection", collection))
                .append("actions", List.of(actions));
        d.runCommand(new Document("createRole", role)
                .append("privileges", List.of(privilege))
                .append("roles", new ArrayList<>()));
    }

    static void createUser(MongoDatabase d, String user, String pwd, String role) {
        d.runCommand(new Document("createUser", user)
                .append("pwd", pwd)
                .append("roles", List.of(new Document("role", role).append("db", DB))));
    }

    static void setup() {
        // 1. Первый администратор (разрешено только пока в базе нет ни одного пользователя)
        try (MongoClient anon = MongoClients.create("mongodb://127.0.0.1:" + PORT)) {
            anon.getDatabase("admin").runCommand(new Document("createUser", ADMIN_USER)
                    .append("pwd", ADMIN_PWD)
                    .append("roles", List.of(new Document("role", "root").append("db", "admin"))));
            System.out.println("Администратор " + ADMIN_USER + " создан.");
        } catch (MongoException e) {
            System.out.println("Администратор уже существует, продолжаем.");
        }

        // 2. Данные, роли и пользователи (под администратором)
        String uri = "mongodb://" + ADMIN_USER + ":" + ADMIN_PWD + "@127.0.0.1:" + PORT + "/?authSource=admin";
        try (MongoClient admin = MongoClients.create(uri)) {
            MongoDatabase d = admin.getDatabase(DB);

            for (String u : new String[]{"lib_viewer", "lib_editor", "lib_auditor"}) {
                try { d.runCommand(new Document("dropUser", u)); } catch (MongoException ignored) { }
            }
            for (String r : new String[]{"libraryViewer", "libraryEditor", "libraryAuditor"}) {
                try { d.runCommand(new Document("dropRole", r)); } catch (MongoException ignored) { }
            }

            d.getCollection("books").deleteMany(new Document());
            d.getCollection("loans").deleteMany(new Document());
            d.getCollection("audit_events").deleteMany(new Document());

            d.getCollection("books").insertMany(docs(
                    "{bookId:1,title:'NoSQL Basics',author:'A. Ivanov',year:2020,copies:5}",
                    "{bookId:2,title:'MongoDB in Practice',author:'B. Petrova',year:2021,copies:3}",
                    "{bookId:3,title:'Data Modeling',author:'C. Sidorov',year:2019,copies:4}",
                    "{bookId:4,title:'Distributed Systems',author:'D. Karimov',year:2018,copies:2}",
                    "{bookId:5,title:'Security Fundamentals',author:'E. Nurlan',year:2022,copies:6}",
                    "{bookId:6,title:'Python for Data',author:'F. Smirnova',year:2020,copies:7}",
                    "{bookId:7,title:'Algorithms',author:'G. Omarov',year:2017,copies:3}",
                    "{bookId:8,title:'Databases Theory',author:'H. Lee',year:2016,copies:2}",
                    "{bookId:9,title:'Cloud Computing',author:'I. Kim',year:2023,copies:5}",
                    "{bookId:10,title:'Web Development',author:'J. Brown',year:2021,copies:4}"));

            d.getCollection("loans").insertMany(docs(
                    "{loanId:1,bookId:1,reader:'reader-001',dateOut:'2026-09-01',dateDue:'2026-09-15'}",
                    "{loanId:2,bookId:2,reader:'reader-002',dateOut:'2026-09-02',dateDue:'2026-09-16'}",
                    "{loanId:3,bookId:3,reader:'reader-003',dateOut:'2026-09-03',dateDue:'2026-09-17'}",
                    "{loanId:4,bookId:5,reader:'reader-004',dateOut:'2026-09-05',dateDue:'2026-09-19'}",
                    "{loanId:5,bookId:6,reader:'reader-005',dateOut:'2026-09-06',dateDue:'2026-09-20'}",
                    "{loanId:6,bookId:7,reader:'reader-006',dateOut:'2026-09-08',dateDue:'2026-09-22'}",
                    "{loanId:7,bookId:9,reader:'reader-007',dateOut:'2026-09-09',dateDue:'2026-09-23'}",
                    "{loanId:8,bookId:10,reader:'reader-008',dateOut:'2026-09-10',dateDue:'2026-09-24'}",
                    "{loanId:9,bookId:4,reader:'reader-009',dateOut:'2026-09-12',dateDue:'2026-09-26'}",
                    "{loanId:10,bookId:8,reader:'reader-010',dateOut:'2026-09-13',dateDue:'2026-09-27'}"));

            d.getCollection("audit_events").insertMany(docs(
                    "{event:'seed',source:'lab',ts:'2026-09-01T09:00:00Z'}",
                    "{event:'catalog_update',source:'lib_editor',ts:'2026-09-02T10:15:00Z'}",
                    "{event:'login',source:'lib_viewer',ts:'2026-09-03T11:30:00Z'}",
                    "{event:'catalog_insert',source:'lib_editor',ts:'2026-09-04T12:45:00Z'}",
                    "{event:'report_view',source:'lib_auditor',ts:'2026-09-05T14:00:00Z'}"));

            createRole(d, "libraryViewer", "books", "find");
            createRole(d, "libraryEditor", "books", "find", "insert", "update", "remove");
            createRole(d, "libraryAuditor", "audit_events", "find");

            createUser(d, "lib_viewer", PW_VIEWER, "libraryViewer");
            createUser(d, "lib_editor", PW_EDITOR, "libraryEditor");
            createUser(d, "lib_auditor", PW_AUDITOR, "libraryAuditor");

            System.out.println("База подготовлена: books=" + d.getCollection("books").countDocuments()
                    + ", loans=" + d.getCollection("loans").countDocuments()
                    + ", audit_events=" + d.getCollection("audit_events").countDocuments()
                    + "; роли и пользователи созданы.");
        }
    }

    // ------------------------------------------------------------ тесты

    static MongoClient connect(String user, String password) {
        MongoCredential credential = MongoCredential.createCredential(user, DB, password.toCharArray());
        MongoClientSettings settings = MongoClientSettings.builder()
                .credential(credential)
                .applyToClusterSettings(b -> b
                        .hosts(List.of(new ServerAddress("127.0.0.1", PORT)))
                        .serverSelectionTimeout(5, TimeUnit.SECONDS))
                .build();
        return MongoClients.create(settings);
    }

    static void runTests() {
        try (MongoClient viewerClient = connect("lib_viewer", PW_VIEWER);
             MongoClient editorClient = connect("lib_editor", PW_EDITOR);
             MongoClient auditorClient = connect("lib_auditor", PW_AUDITOR)) {

            MongoDatabase viewer = viewerClient.getDatabase(DB);
            MongoDatabase editor = editorClient.getDatabase(DB);
            MongoDatabase auditor = auditorClient.getDatabase(DB);

            System.out.printf("%-4s %-12s %-24s %-10s %-22s %s%n",
                    "№", "Пользователь", "Действие", "Ожидалось", "Фактически", "Вывод");
            System.out.println("-".repeat(88));

            // lib_viewer
            check("T1", "lib_viewer", "find в books", true,
                    () -> viewer.getCollection("books").find(eq("bookId", 1)).first());
            check("T2", "lib_viewer", "insert в books", false,
                    () -> viewer.getCollection("books").insertOne(new Document("bookId", 99).append("title", "Test")));
            check("T3", "lib_viewer", "find в loans", false,
                    () -> viewer.getCollection("loans").find(eq("loanId", 1)).first());
            check("T4", "lib_viewer", "find в audit_events", false,
                    () -> viewer.getCollection("audit_events").find().first());

            // lib_editor
            check("T5", "lib_editor", "find в books", true,
                    () -> editor.getCollection("books").find(eq("bookId", 2)).first());
            check("T6", "lib_editor", "insert в books", true,
                    () -> editor.getCollection("books").insertOne(new Document("bookId", 11)
                            .append("title", "New Book").append("author", "K. Test")
                            .append("year", 2026).append("copies", 1)));
            check("T7", "lib_editor", "update в books", true,
                    () -> editor.getCollection("books").updateOne(eq("bookId", 11), set("copies", 2)));
            check("T8", "lib_editor", "delete в books", true,
                    () -> editor.getCollection("books").deleteMany(eq("bookId", 11)));
            check("T9", "lib_editor", "find в loans", false,
                    () -> editor.getCollection("loans").find(eq("loanId", 1)).first());
            check("T10", "lib_editor", "insert в loans", false,
                    () -> editor.getCollection("loans").insertOne(new Document("loanId", 99).append("bookId", 1)));
            check("T11", "lib_editor", "drop books", false,
                    () -> editor.getCollection("books").drop());

            // lib_auditor
            check("T12", "lib_auditor", "find в audit_events", true,
                    () -> auditor.getCollection("audit_events").find().first());
            check("T13", "lib_auditor", "insert в audit_events", false,
                    () -> auditor.getCollection("audit_events").insertOne(new Document("event", "fake")));
            check("T14", "lib_auditor", "find в books", false,
                    () -> auditor.getCollection("books").find().first());
            check("T15", "lib_auditor", "find в loans", false,
                    () -> auditor.getCollection("loans").find().first());

            System.out.println("-".repeat(88));
            System.out.println("Пройдено тестов: " + passed + " из " + total);
        }
    }

    static void check(String id, String user, String action, boolean expectAllowed, Runnable operation) {
        total++;
        String actual;
        boolean ok;
        try {
            operation.run();
            actual = "разрешено";
            ok = expectAllowed;
        } catch (MongoException e) {
            if (e.getCode() == 13) {
                actual = "Unauthorized";
                ok = !expectAllowed;
            } else {
                actual = "ошибка: " + e.getClass().getSimpleName();
                ok = false;
            }
        } catch (Exception e) {
            actual = "ошибка: " + e.getClass().getSimpleName();
            ok = false;
        }
        if (ok) passed++;
        System.out.printf("%-4s %-12s %-24s %-10s %-22s %s%n",
                id, user, action, expectAllowed ? "разрешено" : "запрещено", actual, ok ? "PASS" : "FAIL");
    }
}
