package axoloti;

import axoloti.object.AxoObjectInstanceAbstract;
import java.util.List;

/** Narrow package-level access to serialized legacy graph state. */
public final class SchussPatchAccess {
    private SchussPatchAccess() {
    }

    public static List<AxoObjectInstanceAbstract> objectInstances(Patch patch) {
        return patch.objectInstances;
    }

    /** Invoke the pinned package-private generator without exposing it elsewhere. */
    public static String generateCode(Patch patch) {
        return patch.GenerateCode3();
    }

    public static void initializeSynonyms() {
        if (Synonyms.instance == null) {
            axoloti.utils.AxolotiLibrary factory =
                    axoloti.utils.Preferences.getInstance().getLibrary(
                            axoloti.utils.AxolotiLibrary.AXOLOTI_FACTORY_ID);
            if (factory != null
                    && new java.io.File(factory.getLocalLocation(), Synonyms.filename).isFile()) {
                Synonyms.load();
            }
            if (Synonyms.instance == null) {
                Synonyms.instance = new Synonyms();
            }
        }
    }
}
